import json
import logging
import os
from enum import Enum

from watchdog.events import PatternMatchingEventHandler, DirMovedEvent, FileMovedEvent
from watchdog.observers import Observer

import pluginpaths
from openreadonly import open_shared_read

type ViewItem = list[str]
type ViewItems = list[ViewItem]

class EventType(Enum):
    SELECT = "select"
    TAB = "tab_change"
    BACK = "back"
    NAV = "nav"

class EventSender:
    """Appends JSON formatted events to the MFD event file"""
    def __init__(self, override_event_path=None):
        self.event_sequence = 1
        if not override_event_path:
            self.events_file = pluginpaths.get_events_path()
        else:
            self.events_file = override_event_path
        self.truncate()

    def truncate(self):
        with open(self.events_file, 'w') as file:
            file.truncate()


    def send(self, event_type, tab, index, item_id, label, key):
        line = json.dumps(
            {"seq": self.event_sequence,
             "type": event_type.value,
             "tab": tab,
             "index": index,
             "itemId": item_id,
             "label": label,
             "key": key})
        logging.info(f"Sending event: {line}")
        self.event_sequence += 1
        with open(self.events_file, 'a') as file:
            file.write(line + "\n")

class ScreenFileWatcher(PatternMatchingEventHandler):
    """Watch for changes to the MFD screen JSON file"""
    def __init__(self, edcopilot_json, modified_handler):
        super().__init__(patterns=[os.path.basename(edcopilot_json)])
        self.edcopilot_json = edcopilot_json
        self.modified_handler = modified_handler
        self.observer = Observer(timeout=0.01)


    def start(self):
        self.observer.schedule(self, os.path.dirname(self.edcopilot_json), recursive=True)
        self.observer.start()
        logging.info("File watcher started")

    def stop(self):
        self.observer.stop()

    # Moving a file generates both a move and a delete event when the target file is overwritten
    # Only process the move event to avoid duplicate updates
    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        self.modified_handler()


class ScreenReader:
    """Read the MFD screen JSON file when it changes

    Invokes the callback provided when the data is updated.
    """
    edcopilot_json = pluginpaths.get_screen_path()

    def __init__(self, data_updated, *, override_screen_path=None):
        """"""
        self.data_updated = data_updated

        self.title = ""
        self.subtitle = ""
        self.status = ""
        self.status_color = ""
        self.footer_hint = None

        self.tab_ids = []
        self.tab_data: dict[str, ViewItems] = {}
        self.tab_types = {}
        self.tab_selections = {}

        if override_screen_path:
            self.edcopilot_json = override_screen_path

        self.file_watcher = ScreenFileWatcher(self.edcopilot_json, self.file_modified)


    def start(self):
        self.file_watcher.start()


    def stop(self):
        self.file_watcher.stop()


    def read_screen(self):
        with open_shared_read(self.edcopilot_json) as json_file:
            screen = json.load(json_file)

        self.title = screen['title']
        self.subtitle = screen['subtitle']
        self.status = screen['statusBadge']['text']
        self.status_color = screen['statusBadge']['color']
        self.footer_hint = screen['footerHint']
        self.tab_ids = []

        for tab in screen['tabs']:
            tab_id = tab['id']
            self.tab_ids.append(tab_id)
            # tab_title = tab['title']
            tab_type = tab['type']
            tab_items = tab.get('items')

            if tab_type == "text":
                continue

            selection = None
            if 'defaultSelectedItem' in tab:
                selection = tab['defaultSelectedItem']
            self.tab_selections[tab_id] = selection

            self.tab_types[tab_id] = tab_type

            data = []
            for tab_item in tab_items:
                if tab_type == "list":
                    sublabel = None
                    if 'sublabel' in tab_item:
                        sublabel = tab_item['sublabel']

                    value = None
                    if 'value' in tab_item:
                        value = tab_item['value']

                    data.append([tab_item['id'], tab_item['label'], sublabel, value])
                elif tab_type == "keyvalue":
                    data.append([tab_item['id'], tab_item['key'], '', tab_item['value']])
            self.tab_data[tab_id] = data


    def file_modified(self):
        self.read_screen()
        self.data_updated()


class Client:
    """A simple MFD client with no user interface"""
    def __init__(self, data_loaded, data_changed, *, override_event_path=None, override_screen_path=None):
        self.event_sender = EventSender(override_event_path=override_event_path)
        self.screen_reader = ScreenReader(data_changed, override_screen_path=override_screen_path)
        self.data_loaded = data_loaded
        self.data_changed = data_changed
        self.current_tab = None

        self.log = logging.getLogger(self.__class__.__name__)


    def start(self):
        self.screen_reader.read_screen()
        if self.data_loaded:
            self.data_loaded()
        self.current_tab = self.screen_reader.tab_ids[0]
        self.screen_reader.start()


    def stop(self):
        self.screen_reader.stop()


    def find_item(self, *, item_id=None, item_label=None):
        result = None
        if self.current_tab in self.screen_reader.tab_data:
            data = self.screen_reader.tab_data[self.current_tab]
            index = 0
            for row in data:
                if (item_id and item_id == row[0]) or (item_label and item_label == row[1]):
                    result = [index, row]
                    break
                index += 1

        return result


    def get_item(self, tab_id, index) -> ViewItem:
        length = len(self.screen_reader.tab_data[tab_id])
        if index < length:
            return self.screen_reader.tab_data[tab_id][index]
        else:
            self.log.debug((f"Item index out of range {tab_id} index={index} "
                            f"length={len(self.screen_reader.tab_data[tab_id])}"
                            f" {self.screen_reader.tab_data[tab_id]}"))
            raise IndexError("View item out of bounds")


    def get_item_count(self, tab_id):
        return len(self.screen_reader.tab_data[tab_id])


    def select_item(self, index):
        item = self.get_item(self.current_tab, index)
        if item is not None:
            item_id = item[0]
            item_label = item[1]
            self.log.debug(f"Double click on {self.current_tab}: {index} {item_id} {item_label}")
            self.event_sender.send(EventType.SELECT, self.current_tab, index, item_id, item_label, None)
            self.log.debug("Select event sent")


    def nav_item(self, index):
        item = self.get_item(self.current_tab, index)
        if item:
            item_id = item[0]
            item_label = item[1]
            self.log.debug(f"Single click on {self.current_tab}: {index} {item_id} {item_label}")
            self.event_sender.send(EventType.NAV, self.current_tab, index, item_id, item_label, None)
            self.log.debug("Nav event sent")
        else:
            self.log.debug("Skipping send of nav event for missing item")


    def back(self, index):
        if index:
            item = self.get_item(self.current_tab, index)
            item_id = item[0]
            item_label = item[1]
        else:
            item_id = None
            item_label = None
        self.event_sender.send(EventType.BACK, self.current_tab, index, item_id, item_label, None)
        self.log.debug("Back event sent")


    def switch_tab(self, tab_id):
        self.current_tab = tab_id
        self.event_sender.send(EventType.TAB, self.current_tab,None, None, None, None)
        self.log.debug("Switch tab event sent")