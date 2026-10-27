import unittest

from testing.validation import select_item_index_and_id, validate_back, PlacesPanel, assert_list_item


class ShipPurchaseTestCase(unittest.TestCase):

    def test_ship_purchase(self):
        places_panel = PlacesPanel(self, "ship_purchase")
        panel = places_panel.panel
        view_items = places_panel.view_items
        client = places_panel.client

        selection_history = []

        ship_items = select_item_index_and_id(self, places_panel, "Places", "Places", 6,
                                                       "Ship Purchases", "Ship Purchases",
                                                       None, None, view_items, selection_history,
                                              "Ship Purchases", "",
                                              footer_hint="Waiting for ships available to purchase")
        ship = ship_items[0]
        assert_list_item(self, ship, "Ship List", "1", "Adder", None, None)

        location_items = select_item_index_and_id(self, places_panel, "Places", "Ship List", 6,
                                                   "7", "Asp Explorer", None, None,
                                                  ship_items, selection_history, "Ship Purchases", "Asp Explorer",
                                                  footer_hint="Waiting for locations selling Asp Explorer")


        location = location_items[0]
        assert_list_item(self, location, "Ship Location", "1",
                         "Delkar - de Kamp Orbital (-20% Cargo racks, Hull reinforcements)",
                         "Pad=L, Surface=N",
                         "0 ly + 535 ls")

        # Verify that the default selected items after going back are what was set before selecting the child view
        validate_back(self, panel, selection_history)

        client.validate()


if __name__ == '__main__':
    unittest.main()
