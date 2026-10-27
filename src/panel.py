import hashlib
import json
import logging
import os
import re
import threading
import time

import pluginpaths
from baseview.view import View
from items.item import Item
from views.simpleviews import GuardianTechView, HumanTechView


class Panel:
    """An MFD screen containing multiple tabs"""

    def __init__(self, edcopilot_socket, status, override_screen_path=None):
        self.log = logging.getLogger(self.__class__.__name__)

        self.edcopilot_socket = edcopilot_socket
        self.status = status
        self.tabs = []
        self.tabs_by_id = {}
        self.active_tab: View | None = None
        self.screen = {}
        self.client = None
        self.status_badge = {}
        self.last_json_hash = ""
        self.last_footer_hint = None
        self.tab_level_changed = set()
        self.single_client = None

        # Tracking for tech broker messages sent to the wrong client
        self.technology_broker_client = None
        self.technology_broker_tab = None

        self.json_lock = threading.Lock()
        self.screen_json_path = pluginpaths.get_screen_path()

        if override_screen_path:
            self.screen_json_path = override_screen_path

        if self.edcopilot_socket is not None:
            self.edcopilot_socket.add_completion_handler(self.update_panel_json)
            self.edcopilot_socket.add_disconnect_handler(self.reset_panel)
            self.edcopilot_socket.add_other_client_handler(self.technology_broker_handler)


    def add_tab(self, tab):
        """Add a view to display as a tab"""
        self.tabs.append(tab)
        self.tabs_by_id[tab.view_id] = tab


    def add_data(self, data_type, data):
        """Pass received EDCoPilot data to the currently active tab

        This method is only used with a shared client
        """

        # A few messages are sent immediately after the connection is established that are only needed by the included GUI
        early_messages = {'GUIPREFS', 'GUIFILTERS', 'GUIDATASYNCHED'}
        if self.active_tab is None:
            if not data_type in early_messages:
                self.log.error(f"Attempted to add data without an active tab {data_type}: {data}")
                # raise ValueError(f"Attempted to add data without an active tab {data_type}: {data}")
        else:
            self.add_data_for_tab(self.active_tab, data_type, data)


    @staticmethod
    def add_data_for_tab(tab: View, data_type, data):
        """Pass received EDCoPilot data to the tab that sent the original request

        This method is only used with tab specific clients
        """
        if tab.can_accept_data(data_type):
            tab.add_data(data_type, data)


    def write_initial_screen(self):
        self.update_panel_json()


    def activate_tab(self, tab_id):
        """Called when the user switches to a new tab

        If using a shared client, the new tab is activated to allow sending any EDCoPilot messages needed for the tab
        to functions.  When using tab specific clients, this is not needed as that state is preserved for each client.
        """

        if not self.active_tab or self.active_tab.get_view_id() != tab_id:
            if self.status.is_connected():
                for tab in self.tabs:
                    if tab.get_view_id() == tab_id:
                        if self.single_client is not None:
                            tab.activate_view()
                        self.active_tab = tab
                        break
                self.update_panel_json()


    @staticmethod
    def replace_retry(src, dest):
        """Replace the file with retries for transient Windows errors when another process is reading the file"""
        retries = 20
        while True:
            try:
                os.replace(src, dest)
                return
            except PermissionError as e:
                if retries == 0:
                    raise e
                retries -= 1
                time.sleep(0.25)


    def update_panel_json(self, force_empty_tabs=False):
        """Write and updated JSON screen file with information from the views"""
        self.log.debug("Updating screen file")
        content_updated = False

        if self.status.updated():
            self.status_badge["text"] = self.status.text
            self.status_badge["color"] = self.status.color
            content_updated = True


        self.status_badge["text"]  = self.status.text
        self.status_badge["color"] = self.status.color

        json_tabs = []


        if not self.status.is_connected():
            force_empty_tabs = True

        for tab in self.tabs:
            items = []

            if tab.build_items():
                content_updated = True

            tab_type = tab.get_view_type()

            if not force_empty_tabs:
                self.log.debug(f"Tab {tab.get_view_id()} has {len(tab.get_view_items())} items")
                for tab_item in tab.get_view_items():
                    items.append(tab_item.as_dictionary())

            tab_json = {
                    "id": tab.view_id,
                    "title": tab.view_id,
                    "type": tab_type,
                }

            if tab_type == "text":
                tab_json["text"] = "\n".join(items)
            else:
                tab_json["items"] = items

            default_item = tab.get_selected_item_index()
            if tab.view_id in self.tab_level_changed and default_item is not None and len(items) > 0:
                tab_json["defaultSelectedItem"] = default_item
                self.log.debug(f"Adding default selection: {default_item} to {tab.view_id}")

            json_tabs.append(tab_json)

        footer_hint = None

        if self.active_tab:
            footer_hint = self.active_tab.get_footer_hint()

        if footer_hint != self.last_footer_hint:
            content_updated = True
            self.last_footer_hint = footer_hint

        if not self.status.is_connected():
            footer_hint = self.status.get_disconnected_message()

        title = ""
        if self.active_tab:
            title = self.active_tab.get_title()
        else:
            self.log.warning("No active tab")

        subtitle = ""
        if self.active_tab:
            subtitle = self.active_tab.get_subtitle()


        screen = {
          "$schema": "https://dmnemec.github.io/edvr-mfd/schema/display.v1.schema.json",
          "schemaVersion": 1,
          "title": title,
          "subtitle": subtitle,
          "statusBadge": self.status_badge,
          "footerHint": footer_hint,
          "tabs": json_tabs
        }

        if content_updated:
            with self.json_lock:
                file_contents = json.dumps(screen, indent=4)
                file_hash = hashlib.sha256(file_contents.encode()).hexdigest()

                if file_hash != self.last_json_hash:
                    new_file = self.screen_json_path + ".new"
                    with open(new_file, "w") as file:
                        file.write(file_contents)
                    self.replace_retry(new_file, self.screen_json_path)
                    self.last_json_hash = file_hash
                    self.log.debug("Updated screen file")
                else:
                    self.log.debug("Screen file update not written because the content was unchanged")
        else:
            self.log.debug("Skipping screen file write because the view was unchanged")


    def select_tab_item(self, tab_name, prefixed_item_id):
        """Forward an item selection event to the active view

        Saves the current selection when a new sub-view is created to restore when navigating back.
        """
        submenu_entered = False
        if self.status.is_connected():
            for tab in self.tabs:
                if tab.get_view_id() == tab_name:
                    active_child_id = tab.get_active_view_id()
                    view_id, item_id = Item.split_prefixed_id(prefixed_item_id)
                    if view_id != active_child_id:
                        self.log.error((f"Item id in select event {prefixed_item_id} "
                                        f"does not match the active view {active_child_id}"))
                    else:
                        submenu_entered = tab.select_item(item_id)
                        if submenu_entered:
                            self.tab_level_changed.add(tab_name)
                        self.update_panel_json()
        return submenu_entered


    def back(self):
        """Forwards a back event to the active view"""
        before_view = None
        after_view = None
        back_handled = False
        if self.active_tab:
            before_view = self.active_tab.get_active_view_id()

        if self.status.is_connected():
            if self.active_tab is None:
                raise Exception("Attempted to navigate back with no active tab")
            back_handled = self.active_tab.back()
            if back_handled:
                self.tab_level_changed.add(self.active_tab.view_id)
            self.update_panel_json()

        if self.active_tab:
            after_view = self.active_tab.get_active_view_id()

        if before_view != after_view:
            self.log.debug(f"Back button press changed active view from {before_view} to {after_view}")
        else:
            self.log.debug(f"Back button did not change the active view {before_view}")

        return back_handled


    def reset_panel(self):
        for tab in self.tabs:
            tab.reset_view()

        self.update_panel_json()


    def focus_lost(self):
        """Notifies the active view when a focus_lost event is received"""
        if self.active_tab is not None:
            self.active_tab.focus_lost()

        self.update_panel_json()


    def set_selected_item_index(self, index):
        if self.active_tab is not None:
            self.active_tab.set_selected_item_index(index)
            self.tab_level_changed.discard(self.active_tab.get_view_id())

    def get_selected_item_index(self):
        """Get the index of the selected item in the active view"""
        if self.active_tab is not None:
            self.active_tab.get_selected_item_index()


    def create_single_client(self, message_log_dir=None):
        """Create one socket client for all the tabs to share"""
        client_args = {}
        if message_log_dir:
            client_args["message_log_dir"] = message_log_dir

        self.single_client = self.edcopilot_socket.create_client("main",
                                                          message_handler=self.add_data,
                                                          ready_handler=self._single_client_ready,
                                                          **client_args)

    def _single_client_ready(self):
        threading.Thread(target=self._single_client_activate_tabs, name="Ready").start()

    def _single_client_activate_tabs(self):
        for tab in self.tabs:
            tab.client = self.single_client
            tab.activate_view()
        self.update_panel_json()

    def set_single_client(self, client):
        """Replace the client object for testing"""
        self.single_client = client


    def create_clients(self):
        """Create one socket client for each tab"""
        self.active_tab = self.tabs[0]
        for tab in self.tabs:
            if tab.needs_client():
                client = self.edcopilot_socket.create_client(tab.get_view_id())
                client.message_handler = lambda message_type, message, tab=tab: (
                    self.add_data_for_tab(tab, message_type, message))
                tab.client = client
                client.ready_handler = lambda client=client, tab=tab: self._client_ready(client, tab)


    def _client_ready(self, client, tab):
        # Call activate_view in a background thread to get around the lock that the caller may be holding
        threading.Thread(target=lambda: self._activate_tab(tab), name=("Ready " + client.client_name)).start()


    def _activate_tab(self, tab):
        tab.activate_view()
        self.update_panel_json()


    def technology_broker_handler(self, client_id, content):
        """Process tech broker messages that were incorrectly sent to another client"""
        # The title is sent before the tech broker location details
        if content == "<LOTitle>Technology Brokers":
            for tab in self.tabs:
                active_view_id = tab.get_active_view_id()
                if active_view_id == GuardianTechView.VIEW_ID or active_view_id == HumanTechView.VIEW_ID:
                    self.technology_broker_client = client_id
                    self.technology_broker_tab = tab
                    self.log.debug("Found Technology Broker search result for another client while a tab was waiting for it")
                    break
        elif client_id == self.technology_broker_client:
            # LOBlank is the last message sent in the tech broker query response
            if content.startswith("<LOBlank>"):
                self.technology_broker_client = None
                self.technology_broker_tab = None
            else:
                # Any other messages between LOTitle and LOBlank should be the LOStructure or LOResults content that
                # the waiting view needs.
                match = re.search("^<([a-zA-Z]+)>(.*)", content)
                if match:
                    message_type = match.group(1)
                    message_content = match.group(2)
                    self.log.debug(f"Sending misdirected Technology Broker message to tab {self.technology_broker_tab.view_id}: {message_type} {message_content}")
                    self.technology_broker_tab.add_data(message_type, message_content)