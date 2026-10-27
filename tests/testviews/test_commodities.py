import logging
import unittest

from testing.validation import select_item_index_and_id, assert_labels, validate_back, PlacesPanel, assert_item_ids, \
    assert_list_item


class CommoditiesTestCase(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s')
        self.places_panel = None


    def tearDown(self) -> None:
        self.places_panel.stop()


    def test_commodities(self):
        self.places_panel = PlacesPanel(self, "commodities")
        panel = self.places_panel.panel
        view_items = self.places_panel.view_items
        client = self.places_panel.client
        title = "Commodities"

        selection_history = []

        category_items = select_item_index_and_id(self, self.places_panel, "Places", "Places", 4,
                                                       "Commodities", "Commodities",
                                                       None, None, view_items, selection_history, title, "", footer_hint="Waiting for list of commodities")
        commodity_categories = ["Chemicals", "Consumer Items", "Legal Drugs", "Foods", "Industrial Materials",
                    "Machinery", "Medicines", "Metals", "Minerals", "Rare", "Salvage", "Slaves", "Technology",
                    "Textiles", "Waste", "Weapons"]
        assert_labels(self, category_items, commodity_categories)
        assert_item_ids(self, category_items, commodity_categories)

        commodity_items = select_item_index_and_id(self, self.places_panel,  "Places", "Commodity Categories",
                                                   1, "Consumer Items", "Consumer Items",
                                                   None, None, category_items, selection_history,
                                                   title, "Consumer Items")
        assert_list_item(self, commodity_items[0], "Commodity", "32",
                         "Clothing", None, None)

        transaction_items = select_item_index_and_id(self, self.places_panel, "Places", "Commodity", 0,
                                                     "32", "Clothing", None, None,
                                                     commodity_items, selection_history, title, "Consumer Items / Clothing", original_index=32)
        assert_labels(self, transaction_items,
                      ["Find Closest Buy", "Find Local Buy", "Find Recommended Buy", "Find Closest Sell",
                       "Find Local Sell", "Find Recommended Sell"])
        assert_item_ids(self, transaction_items,
                      ["FindClosestBuy", "FindLocalBuy", "FindRecommendedBuy", "FindClosestSell",
                       "FindLocalSell", "FindRecommendedSell"])

        location_items = select_item_index_and_id(self, self.places_panel, "Places", "Transaction List", 5,
                                                   "FindRecommendedSell", "Find Recommended Sell",
                                                  None, None, transaction_items, selection_history,
                                                  title, "Consumer Items / Clothing / Find Recommended Sell",
                                                  footer_hint="Waiting for commodity locations")


        location = location_items[0]
        assert_list_item(self, location, "Commodity Location", "1",
                         "Col 285 Sector CD-K a38-2 - Luiken Observatory",
                         "Pad=M, Surface=N, Price=2372, Demand=262", "91 ly + 1 ls")

        # Verify that the default selected items after going back are what was set before selecting the child view
        validate_back(self, panel, selection_history)

        client.validate()

    def test_commodities_rare(self):
        self.places_panel = PlacesPanel(self, "commodities_rare")
        panel = self.places_panel.panel
        view_items = self.places_panel.view_items
        client = self.places_panel.client
        title = "Commodities"

        selection_history = []

        category_items = select_item_index_and_id(self, self.places_panel, "Places", "Places", 4,
                                                       "Commodities", "Commodities",
                                                       None, None, view_items, selection_history, title, "", footer_hint="Waiting for list of commodities")
        commodity_categories = ["Chemicals", "Consumer Items", "Legal Drugs", "Foods", "Industrial Materials",
                    "Machinery", "Medicines", "Metals", "Minerals", "Rare", "Salvage", "Slaves", "Technology",
                    "Textiles", "Waste", "Weapons"]
        assert_labels(self, category_items, commodity_categories)
        assert_item_ids(self, category_items, commodity_categories)

        location_items = select_item_index_and_id(self, self.places_panel,  "Places", "Commodity Categories",
                                                   9, "Rare", "Rare",
                                                   None, None, category_items, selection_history,
                                                   title, "Rare", footer_hint="Waiting for rare commodity locations")

        location = location_items[0]
        assert_list_item(self, location, "Commodity Location", "1",
                         "Leesti - George Lucas",
                         "Commodity=Azure Milk, Pad=L, Surface=N, Supply=42", "37 ly + 255 ls")

        # Verify that the default selected items after going back are what was set before selecting the child view
        validate_back(self, panel, selection_history)

        client.validate()

if __name__ == '__main__':
    unittest.main()
