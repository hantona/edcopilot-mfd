import logging
import threading
import time

from eventhandler import EventLogHandler
from items.listitem import ListItem
from journalwatcher import JournalWatcher
from mfdclient.client import Client
from panel import Panel
from spansh_systems import SpanshSystems
from status import Status
from systemname import SystemNameListener
from testing.replayclient import ReplayClient
from testing.testdata import test_file_path, temp_path
from views.informationview import InformationView
from views.placesview import PlacesView


# Helper functions for tests

# Select an item in the list
# Validates that the item is in the previous list result with the expected attributes
# Asserts that the switch succeeded and returns the items in the new view
def select_item_index_and_id[T](test,
                                test_panel: TestPanel,
                                tab_id,
                                view_id,
                                item_index,
                                item_id,
                                item_label,
                                item_sublabel,
                                item_value,
                                view_items: list[ListItem],
                                selection_history,
                                title,
                                subtitle,
                                *, original_index=None,
                                view_type: type[T] = ListItem,
                                footer_hint=None,
                                expecting_more_data=False,
                                ) -> list[T]:

    test_panel.footer_hint_before_receive = None

    panel = test_panel.panel
    if panel.active_tab is None:
        raise Exception("Panel active tab is None")

    # Append the index to a list that can be used to validate the positions when going back.
    # The list won't be accurate for test that mix select and back, but it will avoid simplify tests that select first
    # and then go back.
    selection_history.append(item_index)

    if original_index is None:
        original_index = item_index + 1

    if item_index >= len(view_items):
        test.fail(f"Item index out of range {item_index} >= {len(view_items)}")

    view_item = view_items[item_index]
    test.assertEqual(item_id, view_item.item_id)
    test.assertEqual(view_id, view_item.view_id)
    test.assertEqual(item_label, view_item.label)
    test.assertEqual(item_sublabel, view_item.sublabel)
    test.assertEqual(item_value, view_item.value)
    test.assertEqual(original_index, view_item.original_index)
    panel.set_selected_item_index(item_index)

    test.assertTrue(panel.select_tab_item(tab_id, f"{view_id}_{item_id}"))
    test.assertEqual(0, panel.active_tab.get_selected_item_index())
    panel.active_tab.build_items()
    items = panel.active_tab.get_view_items()

    for item in items:
        test.assertTrue(isinstance(item, view_type))

    if footer_hint is not None:
        # The footer should be set, but not the items
        test.assertEqual(footer_hint, panel.active_tab.get_footer_hint())

        # Release the data before getting the items and verifying that the footer cleared
        test_panel.client.response_wait.set()
        while test_panel.client.response_wait.is_set():
            time.sleep(0.01)

        panel.active_tab.build_items()
        items = panel.active_tab.get_view_items()
        test.assertIsNone(panel.active_tab.get_footer_hint())
    else:
        test.assertIsNone(test_panel.footer_hint_before_receive)
        if expecting_more_data:
            test_panel.client.response_wait.set()
            while test_panel.client.response_wait.is_set():
                time.sleep(0.01)

    test.assertEqual(title, panel.active_tab.get_title())
    test.assertEqual(subtitle, panel.active_tab.get_subtitle())

    return items


# Validate that the labels in the item list match an expected list
def assert_labels(test, items, expected_labels):
    labels = []

    for item in items:
        labels.append(item.label)

    test.assertEqual(expected_labels, labels)


# Validate that the labels in the item list returned from the client match an expected list
def assert_labels_client(test, items, expected_labels):
    labels = []

    for item in items:
        labels.append(item[1])

    test.assertEqual(expected_labels, labels)


def assert_item_ids(test, items, expected_ids):
    ids = []

    for item in items:
        ids.append(item.item_id)

    test.assertEqual(expected_ids, ids)

def assert_item_ids_client(test, view_id, items, expected_ids):
    ids = []

    expected_ids_with_view = [view_id + "_" + x for x in expected_ids]

    for item in items:
        ids.append(item[0])

    test.assertEqual(expected_ids_with_view, ids)

def assert_list_item(test, item: ListItem, expected_view_id, expected_item_id, expected_label,
                     expected_sublabel, expected_value):
    """Validates that the attributes of the list item match the expected values"""
    test.assertEqual(expected_view_id, item.view_id)
    test.assertEqual(expected_item_id, item.item_id)
    test.assertEqual(expected_label, item.label)
    test.assertEqual(expected_sublabel, item.sublabel)
    test.assertEqual(expected_value, item.value)


def assert_list_item_client(test, item: list[str], expected_view_id, expected_item_id, expected_label,
                     expected_sublabel, expected_value):
    """Validates that the attributes of the list item match the expected values"""
    test.assertEqual(expected_view_id + "_" + expected_item_id, item[0])
    test.assertEqual(expected_label, item[1])
    test.assertEqual(expected_sublabel, item[2])
    test.assertEqual(expected_value, item[3])

def validate_back(test, panel, expected_selections):
    """Calls back repeatedly and verifies that the selected item is restored each time"""
    reverse_selections = reversed(expected_selections)
    panel.set_selected_item_index(100)
    for selection in reverse_selections:
        test.assertTrue(panel.back())
        test.assertEqual(selection, panel.active_tab.get_selected_item_index())

        panel.single_client.response_wait.set()

    # The tab should be at the top level and not accept another back
    test.assertFalse(panel.back())


class TestPanel:
    """Test setup for integration tests using one top level tab"""
    def __init__(self, test, test_data_dir, tab_name, default_ship=None, default_system=None):
        self.log = logging.getLogger(self.__class__.__name__)
        panel_path = str(temp_path() / "edcopilot.json")
        event_path = str(temp_path() / "events.jsonl")
        self.test = test
        self.global_lock = threading.Lock()
        self.status = Status()
        self.status.connected = True
        self.panel = Panel(None, self.status, override_screen_path=panel_path)

        self.client = ReplayClient(lambda data_type, data: self.panel.add_data(data_type, data), test,
                                 test_file_path(test_data_dir), self.global_lock, self.panel, pre_response_hook=self.save_footer_hint)
        self.panel.set_single_client(self.client)
        self.system_name_listener = SystemNameListener()
        self.system_name_listener.system_name = default_system

        self.journal_watcher = JournalWatcher()
        self.journal_watcher.ship_name = default_ship

        self.footer_hint_before_receive = None

        self.mfd_data_changes = threading.Event()
        self.mfd_footers = []
        self.mfd_client = Client(None, self.mfd_client_data_changed, override_screen_path=panel_path, override_event_path=event_path)

        self.event_handler = EventLogHandler(self.panel, self.global_lock, override_event_path=event_path)
        self.event_handler.start()

        self.spansh_systems = SpanshSystems(stations_file=test_file_path("EDCoPilot.SpanshSystems.txt"))

        if tab_name == "Places":
            places_view = PlacesView(self.journal_watcher, self.spansh_systems)
            places_view.client = self.client
            self.panel.add_tab(places_view)
            self.panel.activate_tab("Places")

            # Release the location search response needed by Places
            self.client.response_wait.set()
            while self.client.response_wait.is_set():
                time.sleep(0.01)
            self.panel.update_panel_json()
        elif tab_name == "Information":
            information_view = InformationView(system_name_listener=self.system_name_listener)
            information_view.client = self.client
            self.panel.add_tab(information_view)
            self.panel.activate_tab("Information")
        else:
            self.test.fail("Invalid tab name")

        if self.panel.active_tab is not None:
            self.panel.active_tab.build_items()
            self.view_items = self.panel.active_tab.get_view_items()
            self.mfd_client.start()
            self.status.mark_connected()
            # self.panel.update_panel_json()
        else:
            raise ValueError("Active panel was None")

    def validate_back_client(self, test, panel, expected_selections):
        """Calls back repeatedly and verifies that the selected item is restored each time"""
        reverse_selections = reversed(expected_selections)
        for selection in reverse_selections:
            if self.panel.active_tab is None:
                raise ValueError("Active tab was none")
            tab_id = self.panel.active_tab.view_id
            count = self.mfd_client.get_item_count(tab_id)
            with self.global_lock:
                self.event_handler.events_processed.clear()
                self.mfd_data_changes.clear()
                self.mfd_client.nav_item(count - 1)
                self.mfd_client.back(count - 1)
                self.client.response_wait.set()
            test.assertTrue(self.event_handler.events_processed.wait(60), "Timed out waiting for events to process")
            test.assertTrue(self.mfd_data_changes.wait(30), "Timed out waiting for mfd data to change")

            test.assertEqual(selection, self.mfd_client.screen_reader.tab_selections[tab_id], "Tab selection didn't match saved selection")

        # The tab should be at the top level and not accept another back
        test.assertFalse(panel.back())

    def stop(self):
        self.mfd_client.stop()
        self.event_handler.stop()
        self.client.close()


    def mfd_client_data_changed(self):
        self.mfd_footers.append(self.mfd_client.screen_reader.footer_hint)
        self.mfd_data_changes.set()


    def set_ship(self, ship):
        self.journal_watcher.ship_name = ship

    def set_system(self, system):
        self.system_name_listener.system_name = system

    def save_footer_hint(self):
        if self.panel.active_tab:
            self.footer_hint_before_receive = self.panel.active_tab.get_footer_hint()

    def select_item_index_and_id_with_client(self,
                                    test,
                                    tab_id,
                                    view_id,
                                    item_index,
                                    item_id,
                                    item_label,
                                    item_sublabel,
                                    item_value,
                                    view_items: list[ListItem],
                                    selection_history,
                                    title,
                                    subtitle,
                                    *,
                                    footer_hint=None,
                                    immediate_results: bool = False,
                                    expecting_more_data: bool = True,
                                    expecting_second_json_update = True,
                                    ):


        mfd_client = self.mfd_client
        if not mfd_client.current_tab:
            raise Exception("Panel active tab is None")

        # test_panel.footer_hint_before_receive = None

        # Append the index to a list that can be used to validate the positions when going back.
        # The list won't be accurate for test that mix select and back, but it will avoid simplify tests that select first
        # and then go back.
        selection_history.append(item_index)

        item_count = mfd_client.get_item_count(mfd_client.current_tab)
        if item_index >= item_count:
            test.fail(f"Item index out of range {item_index} >= {item_count}")

        view_item = mfd_client.get_item(tab_id, item_index)
        test.assertEqual([view_id + "_" + item_id, item_label, item_sublabel, item_value], view_item)

        with self.global_lock:
            # Send the events while holding the lock so that both will be processed before the flag is set
            self.event_handler.events_processed.clear()
            self.mfd_data_changes.clear()
            mfd_client.nav_item(item_index)
            mfd_client.select_item(item_index)

        # Wait for the events to be processed
        self.log.debug("Waiting for events to process")
        test.assertTrue(self.event_handler.events_processed.wait(60), "Timed out waiting for events to process")
        self.log.debug("Events processed")

        # Wait for the panel to be updated with the footer_hint and empty item list or a fixed list
        self.log.debug("Waiting for json update")
        test.assertTrue(self.mfd_data_changes.wait(30), "Timed out waiting for mfd data to change")
        self.log.debug("Json update")

        if immediate_results:
            items = mfd_client.screen_reader.tab_data[tab_id]
            test.assertTrue(len(items) > 0)
            test.assertEqual(footer_hint, mfd_client.screen_reader.footer_hint)
            test.assertEqual(0, mfd_client.screen_reader.tab_selections[tab_id], "Tab selection was not 0")

            if expecting_more_data:
                self.mfd_data_changes.clear()
                self.client.response_wait.set()
                if expecting_second_json_update:
                    self.log.debug("Waiting for json update after receiving data")
                    test.assertTrue(self.mfd_data_changes.wait(30), "Timed out waiting for mfd data to change")
                else:
                    self.log.debug("Waiting for unused data to send")
                    while self.client.response_wait.is_set():
                        time.sleep(0.01)
                test.assertIsNone(mfd_client.screen_reader.footer_hint)
        else:
            items = mfd_client.screen_reader.tab_data[tab_id]
            test.assertEqual(0, len(items))
            test.assertEqual(footer_hint, mfd_client.screen_reader.footer_hint)
            test.assertIsNone(mfd_client.screen_reader.tab_selections[tab_id])

            # Unblock the response sender thread and wait until it calls update_json_panel() with the data
            self.mfd_data_changes.clear()
            self.client.response_wait.set()
            while self.client.response_wait.is_set():
                time.sleep(0.01)
            self.log.debug("Waiting for json update after receiving data")
            test.assertTrue(self.mfd_data_changes.wait(30), "Timed out waiting for mfd data to change")

            items = mfd_client.screen_reader.tab_data[tab_id]
            test.assertTrue(len(items) > 0)
            test.assertIsNone(mfd_client.screen_reader.footer_hint)
            test.assertEqual(0, mfd_client.screen_reader.tab_selections[tab_id], "Tab selection was not 0")

        test.assertEqual(title, mfd_client.screen_reader.title)
        test.assertEqual(subtitle, mfd_client.screen_reader.subtitle)

        return items


class PlacesPanel(TestPanel):
    """Test setup for test using the places tab"""
    def __init__(self, test, test_data_dir, default_ship="Sidewinder Mk I"):
        super().__init__(test, test_data_dir, "Places", default_ship=default_ship)


class InformationPanel(TestPanel):
    """Test setup for test using the information tab"""
    def __init__(self, test, test_data_dir, default_system="Delkar"):
        super().__init__(test, test_data_dir, "Information", default_system=default_system)
