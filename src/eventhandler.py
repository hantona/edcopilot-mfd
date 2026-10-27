import json
import logging
import os
import threading

from watchdog.events import PatternMatchingEventHandler, FileSystemEvent
from watchdog.observers import Observer

import pluginpaths
from items.item import Item
from openreadonly import open_shared_read


class EventLogHandler(PatternMatchingEventHandler):
    """Watch for changes to the MFD event file and process new events"""
    def __init__(self, panel, global_lock, override_event_path=None):
        self.log = logging.getLogger(self.__class__.__name__)
        self.events_json_path = pluginpaths.get_events_path()
        if override_event_path is not None:
            self.events_json_path = override_event_path
        super().__init__(patterns=[os.path.basename(self.events_json_path)])
        self.panel = panel
        self.global_lock = global_lock

        self.last_event_size = None
        self.last_event_seq = 0
        self.observer = None

        self.log.debug("Searching for last event produced before this instance started")
        self._find_last_seq()

        self.lock = threading.Lock()
        self.events_processed = threading.Event()


    def start(self):
        self.observer = Observer(timeout=0.01)
        self.observer.name = "EventWatchdog"
        self.observer.schedule(self, os.path.dirname(self.events_json_path), recursive=False)
        self.observer.start()
        self.log.info(f"Event file watcher started with initial event {self.last_event_seq} in {self.events_json_path}")


    def stop(self):
        self.observer.stop()
        self.observer.join()
        self.observer = None


    def _find_last_seq(self):
        """Scan the event file to find the last event sequence number so preexisting events are not processed"""
        last_event = ""

        try:
            with open_shared_read(self.events_json_path) as file:
                self.last_event_size = os.path.getsize(self.events_json_path)
                while line := file.readline():
                    if line.startswith("{"):
                        last_event = line
        except FileNotFoundError:
            self.log.error("events.jsonl not found")
        except OSError as e:
            self.log.exception("Failure in _find_last_seq", e)

        if last_event:
            event = json.loads(last_event)
            self.last_event_seq = event["seq"]


    def process_new_events(self):
        """Process all events in the events file with sequence numbers larger than the last one processed"""
        try:
            with self.lock:
                self.log.debug(f"process_new_event last {self.last_event_seq} id {id(self)}")
                with open_shared_read(self.events_json_path) as file:
                    new_size = os.path.getsize(self.events_json_path)
                    self.log.debug(f"Log file size is {new_size} was {self.last_event_size}")
                    if new_size < self.last_event_size:
                        # The game was restarted and the events file was truncated
                        self.log.debug("Event file truncated by game restart")
                        self.last_event_seq = 0
                    self.last_event_size = new_size

                    while line := file.readline():
                        if line == "":
                            continue

                        if not line.startswith("{"):
                            continue

                        event = json.loads(line)
                        seq = event["seq"]
                        if seq <= self.last_event_seq:
                            continue

                        self.log.debug(f"Processing new event: {event}")
                        self.last_event_seq = seq
                        with self.global_lock:
                            self.log.debug("Lock acquired")
                            self.handle_event(event)
                        self.log.debug("Lock released")
                self.events_processed.set()
        except Exception as e:
            self.log.exception("Failure in process_new_events", e)


    def handle_event(self, event):
        """Process a single event from the file"""
        if event["type"] == "tab_change":
            if self.panel.active_tab and event["tab"] != self.panel.active_tab.get_view_id():
                self.log.debug(f"Detected change to tab {event['tab']} from {self.panel.active_tab.get_view_id()}")
                self.panel.activate_tab(event["tab"])
        elif event["type"] == "nav":
            # The nav event is sent when the arrow key moves the selection, but can be used to detect the active tab
            # after a companion restart
            if self.panel.active_tab and event["tab"] != self.panel.active_tab.get_view_id():
                self.log.debug(f"Detected change to tab {event['tab']} from {self.panel.active_tab.get_view_id()}")
                self.panel.activate_tab(event["tab"])
            self.panel.set_selected_item_index(event["index"])
        elif event["type"] == "select":
            # Activate the tab if the companion was restarted and the user clicked the active item without scrolling
            if self.panel.active_tab and event["tab"] != self.panel.active_tab.get_view_id():
                self.panel.activate_tab(event["tab"])
            self.log.debug(f"Item selected: {event}")
            old_view = self.panel.active_tab.get_active_view_id()
            prefixed_item_id = event["itemId"]
            tab_id = event["tab"]
            self.panel.select_tab_item(tab_id, prefixed_item_id)
            new_view = self.panel.active_tab.get_active_view_id()
            if old_view != new_view:
                self.log.debug(f"View changed from {old_view} to {new_view}")
            else:
                self.log.debug(f"View is still {new_view} after select")
        elif event["type"] == "back":
            self.log.debug(f"Back button pressed: {event}")
            prefixed_item_id = event["itemId"]
            if prefixed_item_id:
                active_child_id = self.panel.active_tab.get_active_view_id()
                view_id, item_id = Item.split_prefixed_id(prefixed_item_id)
                if view_id != active_child_id:
                    self.log.error(
                        f"Item id in back event {prefixed_item_id} does not match the active view {active_child_id}")
                else:
                    self.panel.back()
            else:
                self.panel.back()
        elif event["type"] in ["nav", "context_changed"]:
            pass
        elif event["type"] == "focus_lost":
            self.panel.focus_lost()
        elif event["type"] != "focus_lost" and event["type"] != "focus_gained":
            self.log.debug(f"Received an Unexpected event {event}")


    def on_any_event(self, event: FileSystemEvent) -> None:
        self.log.debug(f"Received event log file change event: {event}")
        self.process_new_events()
