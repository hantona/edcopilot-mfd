import logging
import signal
import sys
import threading
from pathlib import Path

import pluginpaths
from edcopilot.edcopilotsocket import EDCopilotSocket
from eventhandler import EventLogHandler
from journalwatcher import JournalWatcher
from spansh_systems import SpanshSystems
from views.informationview import InformationView
from panel import Panel
from status import Status
from systemname import SystemNameListener
from views.placesview import PlacesView

from filelock import FileLock, Timeout

from views.voicelog import VoicelogView


class Application:
    def __init__(self, add_shutdown_hook=True, multi_instance_lock=True, message_log_dir=None):
        self.add_shutdown_hook = add_shutdown_hook
        self.multi_instance_lock = multi_instance_lock
        self.message_log_dir = message_log_dir

        self.lock = FileLock(pluginpaths.get_lock_path())

        # Prevent MFD events and EDCopilot messages from processing simultaneously
        self.global_lock = threading.Lock()

        # Watch for changes to the active ship type and bounties
        self.journal_watcher = JournalWatcher()
        self.journal_watcher.start()

        self.status = Status()
        self.edcopilot_socket = EDCopilotSocket(self.status, self.global_lock)
        self.panel = Panel(self.edcopilot_socket, self.status)

        self.system_name_listener = SystemNameListener()
        self.edcopilot_socket.add_broadcast_handler(self.system_name_listener.broadcast_handler)
        self.edcopilot_socket.add_broadcast_handler(self.voicelog_broadcast_handler)

        self.spansh_systems = SpanshSystems()

        self.voicelog_view = VoicelogView()

        self.panel.add_tab(PlacesView(self.journal_watcher, self.spansh_systems))
        self.panel.add_tab(InformationView(self.system_name_listener))
        self.panel.add_tab(self.voicelog_view)
        self.panel.activate_tab("Places")

        if self.message_log_dir:
            Path(self.message_log_dir).mkdir(parents=True, exist_ok=True)
            self.panel.create_single_client(message_log_dir=self.message_log_dir)
        else:
            self.panel.create_clients()

        self.event_handler = EventLogHandler(self.panel, self.global_lock)


    def voicelog_broadcast_handler(self, message):
        self.voicelog_view.append_log_line(message)

    def multiple_instance_check(self):
        try:
            pass
            self.lock.acquire(timeout=0.0001)
        except Timeout:
            logging.info("Another process is running.")
            raise RuntimeError("Another process is running.")

    def run(self):
        if self.multi_instance_lock:
            self.multiple_instance_check()

        self.panel.write_initial_screen()

        if self.add_shutdown_hook:
            signal.signal(signal.SIGTERM, self.handle_interrupt)
            signal.signal(signal.SIGINT, self.handle_interrupt)
            signal.signal(signal.SIGBREAK, self.handle_interrupt)

        self.event_handler.start()
        self.edcopilot_socket.start()


    def stop(self):
        # Stop all the background threads so the process will exit
        self.edcopilot_socket.stop()
        self.event_handler.stop()
        self.panel.update_panel_json()
        self.journal_watcher.stop()
        self.lock.release()


    def handle_interrupt(self, _signum, _frame):
        self.stop()
        sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s')
    message_log_argument = None
    if len(sys.argv) == 2:
        message_log_argument = sys.argv[1]
    Application(message_log_dir=message_log_argument).run()