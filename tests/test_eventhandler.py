import threading
import unittest
from unittest.mock import MagicMock

from testing.testdata import temp_path

from eventhandler import EventLogHandler


class EventHandlerTest(unittest.TestCase):
    def setUp(self):
        self.event_path = temp_path() / "events.jsonl"
        if self.event_path.exists():
            self.event_path.unlink()
        self.event_path.touch()

        self.panel = MagicMock()
        self.panel.active_tab = MagicMock()

        self.panel.select_tab_item = MagicMock()
        self.panel.back = MagicMock()
        self.panel.set_selected_item_index = MagicMock()
        self.panel.focus_lost = MagicMock()
        self.panel.activate_tab = MagicMock()

        self.event_log_handler = EventLogHandler(self.panel, threading.Lock(), override_event_path=str(self.event_path))
        self.event_log_handler.start()

    def tearDown(self):
        self.event_log_handler.stop()
        if self.event_path.exists():
            self.event_path.unlink()

    def test_select(self):
        current_view_id = "Places"
        self.panel.active_tab.get_view_id = MagicMock(return_value=current_view_id)

        # Pass in a select event with a tab that matches the current tab
        # selecte_tab_item will be called, but not activate_tab
        self.event_log_handler.events_processed.clear()
        self.append_event('{"seq": 3, "type": "select", "tab": "Places", "index": 4, "itemId": "Places_Commodities", "label": "Commodities", "key": null}')
        self.event_log_handler.events_processed.wait(10)

        self.panel.select_tab_item.assert_called_with("Places", "Places_Commodities")
        self.panel.back.assert_not_called()
        self.panel.set_selected_item_index.assert_not_called()
        self.panel.focus_lost.assert_not_called()
        self.panel.activate_tab.assert_not_called()


    def test_select_new_tab(self):
        current_view_id = "Information"
        self.panel.active_tab.get_view_id = MagicMock(return_value=current_view_id)

        # Pass a select event with a tab id different from the one already set
        # The new tab should be activated in addition to processing the item selection
        self.event_log_handler.events_processed.clear()
        self.append_event('{"seq": 3, "type": "select", "tab": "Places", "index": 4, "itemId": "Places_Commodities", "label": "Commodities", "key": null}')
        self.event_log_handler.events_processed.wait(10)

        self.panel.select_tab_item.assert_called_with("Places", "Places_Commodities")
        self.panel.back.assert_not_called()
        self.panel.set_selected_item_index.assert_not_called()
        self.panel.focus_lost.assert_not_called()
        self.panel.activate_tab.assert_called_with("Places")


    def test_back(self):
        current_view_id = "Places"
        self.panel.active_tab.get_view_id = MagicMock(return_value=current_view_id)

        # self.append_event('{"seq": 180, "type": "nav", "tab": "Places", "index": 4, "itemId": "Places_Commodities", "label": "Commodities", "key": null}')
        self.event_log_handler.events_processed.clear()
        self.append_event('{"seq": 16, "type": "back", "tab": "Places", "index": null, "itemId": null, "label": null, "key": null}')
        self.event_log_handler.events_processed.wait(10)

        self.panel.select_tab_item.assert_not_called()
        self.panel.back.assert_called()
        self.panel.set_selected_item_index.assert_not_called()
        self.panel.focus_lost.assert_not_called()
        self.panel.activate_tab.assert_not_called()


    def test_nav(self):
        current_view_id = "Places"
        self.panel.active_tab.get_view_id = MagicMock(return_value=current_view_id)

        self.event_log_handler.events_processed.clear()
        self.append_event('{"seq": 180, "type": "nav", "tab": "Places", "index": 4, "itemId": "Places_Commodities", "label": "Commodities", "key": null}')
        self.event_log_handler.events_processed.wait(10)

        self.panel.select_tab_item.assert_not_called()
        self.panel.back.assert_not_called()
        self.panel.set_selected_item_index.assert_called_with(4)
        self.panel.focus_lost.assert_not_called()
        self.panel.activate_tab.assert_not_called()

    def test_nav_new_tab(self):
        current_view_id = "Information"
        self.panel.active_tab.get_view_id = MagicMock(return_value=current_view_id)

        self.event_log_handler.events_processed.clear()
        self.append_event(
            '{"seq": 180, "type": "nav", "tab": "Places", "index": 4, "itemId": "Places_Commodities", "label": "Commodities", "key": null}')
        self.event_log_handler.events_processed.wait(10)

        self.panel.select_tab_item.assert_not_called()
        self.panel.back.assert_not_called()
        self.panel.set_selected_item_index.assert_called_with(4)
        self.panel.focus_lost.assert_not_called()
        self.panel.activate_tab.assert_called_with("Places")


    def test_focus_lost(self):
        current_view_id = "Places"
        self.panel.active_tab.get_view_id = MagicMock(return_value=current_view_id)

        # focus_lost event calls focus_lost
        self.event_log_handler.events_processed.clear()
        self.append_event('{"seq": 180, "type": "focus_lost", "tab": "Places", "index": 4, "itemId": "Places_Commodities", "label": "Commodities", "key": null}')
        self.event_log_handler.events_processed.wait(10)

        self.panel.select_tab_item.assert_not_called()
        self.panel.back.assert_not_called()
        self.panel.set_selected_item_index.assert_not_called()
        self.panel.focus_lost.assert_called()
        self.panel.activate_tab.assert_not_called()

    def test_tab_change(self):
        current_view_id = "Places"
        self.panel.active_tab.get_view_id = MagicMock(return_value=current_view_id)

        # Send a tab_change event with the same tab id already set
        # The call to activate_tab will be skipped
        self.event_log_handler.events_processed.clear()
        self.append_event('{"seq": 1, "type": "tab_change", "tab": "Places", "index": null, "itemId": null, "label": null, "key": null}')
        self.event_log_handler.events_processed.wait(10)

        self.panel.select_tab_item.assert_not_called()
        self.panel.back.assert_not_called()
        self.panel.set_selected_item_index.assert_not_called()
        self.panel.focus_lost.assert_not_called()
        self.panel.activate_tab.assert_not_called()


    def test_tab_change_new_tab(self):
        current_view_id = "Information"
        self.panel.active_tab.get_view_id = MagicMock(return_value=current_view_id)

        # Send a tab_change event with a tab id different from the one currently set
        # activate_tab will be called with the new tab id
        self.event_log_handler.events_processed.clear()
        self.append_event(
            '{"seq": 1, "type": "tab_change", "tab": "Places", "index": null, "itemId": null, "label": null, "key": null}')
        self.event_log_handler.events_processed.wait(10)

        self.panel.select_tab_item.assert_not_called()
        self.panel.back.assert_not_called()
        self.panel.set_selected_item_index.assert_not_called()
        self.panel.focus_lost.assert_not_called()
        self.panel.activate_tab.assert_called_with("Places")


    def append_event(self, event):
        with open(self.event_path, "a") as f:
            f.write("{}\n".format(event))


if __name__ == '__main__':
    unittest.main()
