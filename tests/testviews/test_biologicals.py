import unittest

from testing.validation import validate_back, select_item_index_and_id, InformationPanel, assert_list_item

class BiologicalsTestCase(unittest.TestCase):

    def setUp(self):
        self.information_panel = InformationPanel(self, "biologicals")


    def tearDown(self) -> None:
        self.information_panel.stop()


    def test_biologicals(self):
        panel = self.information_panel.panel
        view_items = self.information_panel.view_items
        client = self.information_panel.client

        selection_history = []

        biologicals_view = select_item_index_and_id(self, self.information_panel, "Information", "Information", 3,
                                                     "Biologicals", "Biologicals",
                                                     None, None, view_items, selection_history, "Biologicals", "",
                                                    footer_hint="Waiting for known biological signals")
        item = biologicals_view[0]
        assert_list_item(self, item, "Biologicals",
                         "Delkar|Delkar 7 d|Bacterium Aurasus - Emerald",
                         "Delkar 7 d - Bacterium Aurasus - Emerald",
                         "Scanned CR= ,HIST=0", "1,000,000")

        validate_back(self, panel, selection_history)
        client.validate()


if __name__ == '__main__':
    unittest.main()
