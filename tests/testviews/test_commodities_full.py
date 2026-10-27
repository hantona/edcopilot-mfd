import logging
import unittest

from testing.validation import PlacesPanel, assert_labels_client, assert_item_ids_client, assert_list_item_client


# A variant of the commodity view test that controls and validates the view through the MFD event and screen file
class CommoditiesFullTest(unittest.TestCase):

    def setUp(self) -> None:
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

        category_items = self.places_panel.select_item_index_and_id_with_client(self, "Places", "Places", 4,
                                                       "Commodities", "Commodities",
                                                       None, None, view_items, selection_history, title, "", footer_hint="Waiting for list of commodities",
                                                                                immediate_results=True)
        commodity_categories = ["Chemicals", "Consumer Items", "Legal Drugs", "Foods", "Industrial Materials",
                    "Machinery", "Medicines", "Metals", "Minerals", "Rare", "Salvage", "Slaves", "Technology",
                    "Textiles", "Waste", "Weapons"]
        assert_labels_client(self, category_items, commodity_categories)
        assert_item_ids_client(self, "Commodity Categories", category_items, commodity_categories)

        commodity_items = self.places_panel.select_item_index_and_id_with_client(self, "Places", "Commodity Categories",
                                                   1, "Consumer Items", "Consumer Items",
                                                   None, None, category_items, selection_history,
                                                   title, "Consumer Items", immediate_results=True,
                                                                                 expecting_more_data=False)
        assert_list_item_client(self, commodity_items[0], "Commodity", "32",
                         "Clothing", None, None)

        transaction_items = self.places_panel.select_item_index_and_id_with_client(self, "Places", "Commodity", 0,
                                                     "32", "Clothing", None, None,
                                                     commodity_items, selection_history, title, "Consumer Items / Clothing", immediate_results=True, expecting_second_json_update=False,
                                                                                   expecting_more_data=False)
        assert_labels_client(self, transaction_items,
                      ["Find Closest Buy", "Find Local Buy", "Find Recommended Buy", "Find Closest Sell",
                       "Find Local Sell", "Find Recommended Sell"])
        assert_item_ids_client(self, "Transaction List", transaction_items,
                      ["FindClosestBuy", "FindLocalBuy", "FindRecommendedBuy", "FindClosestSell",
                       "FindLocalSell", "FindRecommendedSell"])

        location_items = self.places_panel.select_item_index_and_id_with_client(self, "Places", "Transaction List", 5,
                                                   "FindRecommendedSell", "Find Recommended Sell",
                                                  None, None, transaction_items, selection_history,
                                                  title, "Consumer Items / Clothing / Find Recommended Sell",
                                                                                footer_hint="Waiting for commodity locations")


        location = location_items[0]
        assert_list_item_client(self, location, "Commodity Location", "1",
                         "Col 285 Sector CD-K a38-2 - Luiken Observatory",
                         "Pad=M, Surface=N, Price=2372, Demand=262", "91 ly + 1 ls")

        # Verify that the default selected items after going back are what was set before selecting the child view
        self.places_panel.validate_back_client(self, panel, selection_history)

        client.validate()

    def test_commodities_rare(self):
        self.places_panel = PlacesPanel(self, "commodities_rare")
        panel = self.places_panel.panel
        view_items = self.places_panel.view_items
        client = self.places_panel.client
        title = "Commodities"

        selection_history = []

        category_items = self.places_panel.select_item_index_and_id_with_client(self, "Places", "Places", 4,
                                                       "Commodities", "Commodities",
                                                       None, None, view_items, selection_history, title, "", footer_hint="Waiting for list of commodities",
                                                  immediate_results=True)
        commodity_categories = ["Chemicals", "Consumer Items", "Legal Drugs", "Foods", "Industrial Materials",
                    "Machinery", "Medicines", "Metals", "Minerals", "Rare", "Salvage", "Slaves", "Technology",
                    "Textiles", "Waste", "Weapons"]
        assert_labels_client(self, category_items, commodity_categories)
        assert_item_ids_client(self, "Commodity Categories", category_items, commodity_categories)

        location_items = self.places_panel.select_item_index_and_id_with_client(self, "Places", "Commodity Categories",
                                                   9, "Rare", "Rare",
                                                   None, None, category_items, selection_history,
                                                   title, "Rare", footer_hint="Waiting for rare commodity locations")

        location = location_items[0]
        assert_list_item_client(self, location, "Commodity Location", "1",
                         "Leesti - George Lucas",
                         "Commodity=Azure Milk, Pad=L, Surface=N, Supply=42", "37 ly + 255 ls")

        # Verify that the default selected items after going back are what was set before selecting the child view
        self.places_panel.validate_back_client(self, panel, selection_history)

        client.validate()

if __name__ == '__main__':
    unittest.main()
