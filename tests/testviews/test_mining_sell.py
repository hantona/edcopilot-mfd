import unittest

from testing.validation import validate_back, select_item_index_and_id, assert_labels, InformationPanel, \
    assert_list_item


class MiningSellTestCase(unittest.TestCase):
    def setUp(self):
        self.information_panel = InformationPanel(self, "mining_sell")


    def tearDown(self) -> None:
        self.information_panel.stop()


    def test_mining_sell(self):
        panel = self.information_panel.panel
        view_items = self.information_panel.view_items
        client = self.information_panel.client

        selection_history = []

        category_items = select_item_index_and_id(self, self.information_panel, "Information", "Information", 5,
                                               "Mining Sell", "Mining Sell", None,
                                               None, view_items, selection_history, "Mining Sell", "",
                                                  footer_hint="Waiting for list of mining materials")

        assert_labels(self, category_items, ["Core", "Laser", "Surface"])

        material_items = select_item_index_and_id(self, self.information_panel, "Information", "Mining Sell List Categories",
                                                  1, "Laser", "Laser", None,
                                                  None, category_items, selection_history, "Mining Sell", "Laser")

        assert_list_item(self, material_items[0], "Mining Sell List", "Painite",
                         "Painite", None, "528,968")
        prices = [int(x.value.replace(",", "")) for x in material_items]
        sorted_prices = sorted(prices, reverse=True)
        self.assertEqual(sorted_prices, prices, "prices should be in descending order")
        location_items = select_item_index_and_id(self, self.information_panel, "Information", "Mining Sell List", 1,
                                                  "Platinum", "Platinum", None,
                                                  "302,844", material_items, selection_history,
                                                  "Mining Sell", "Laser / Platinum",
                                                  footer_hint="Waiting for list of locations to sell Platinum",
                                                  original_index=39)

        location = location_items[0]
        assert_list_item(self, location, "Mining Sell Search", "1",
                         "Col 285 Sector CG-O d6-118 - Buckley Liberty", "Pad=L, Surface=Y, Price=302844, Supply=4493",
                         "206 ly + 717 ls")

        client.validate()

        # Verify that the default selected items after going back are what was set before selecting the child view
        validate_back(self, panel, selection_history)


if __name__ == '__main__':
    unittest.main()
