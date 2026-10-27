import unittest

from items.keyvalueitem import KeyValueItem
from testing.validation import select_item_index_and_id, validate_back, InformationPanel

class SystemDataTestCase(unittest.TestCase):
    def setUp(self):
        self.information_panel = InformationPanel(self, "system_data")


    def tearDown(self) -> None:
        self.information_panel.stop()


    def test_stations(self):
        panel = self.information_panel.panel
        view_items = self.information_panel.view_items
        client = self.information_panel.client

        selection_history = []

        system_data_items = select_item_index_and_id(self, self.information_panel, "Information", "Information", 0,
                                                     "System Data", "System Data",
                                                     None, None, view_items, selection_history,
                                                     title="System Data", subtitle="",
                                                     footer_hint="Waiting for system data",
                                                     view_type=KeyValueItem)
        item = system_data_items[0]
        self.assertEqual("System Data", item.view_id)
        self.assertEqual("System Name", item.item_id)
        self.assertEqual("System Name", item.key)
        self.assertEqual("Delkar (CURRENT LOCATION)", item.value)

        validate_back(self, panel, selection_history)

        client.validate()


if __name__ == '__main__':
    unittest.main()
