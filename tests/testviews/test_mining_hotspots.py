import unittest

from testing.validation import validate_back, select_item_index_and_id, InformationPanel, assert_list_item


class MiningHotspotsTestCase(unittest.TestCase):
    def setUp(self):
        self.information_panel = InformationPanel(self, "mining_hotspot")


    def tearDown(self) -> None:
        self.information_panel.stop()


    def test_hotspots(self):
        panel = self.information_panel.panel
        view_items = self.information_panel.view_items
        client = self.information_panel.client

        selection_history = []

        material_items = select_item_index_and_id(self, self.information_panel, "Information", "Information", 4,
                                                  "Mining Hotspots", "Mining Hotspots", None,
                                                  None, view_items, selection_history, "Mining Hotspots",
                                                  "", footer_hint="Waiting for list of mining hotspot materials")
        assert_list_item(self, material_items[0], "Mining Hotspots List", "Musgravite", "Musgravite", None, "978,294")

        last_price = None
        for material_item in material_items:
            price = int(material_item.value.replace(",", ""))

            if last_price and last_price < price:
                self.fail("Hotspot list not sorted by price")
            last_price = price

        location_items = select_item_index_and_id(self, self.information_panel, "Information", "Mining Hotspots List", 9,
                                                  "Platinum", "Platinum", None,
                                                  "302,844", material_items, selection_history,
                                                  "Mining Hotspots", "Platinum", original_index=39,
                                                  footer_hint="Waiting for nearby Platinum hotspots")

        location = location_items[0]
        assert_list_item(self, location, "Mining Search", "1",
                         "Delkar (7 A Ring) - MINED",
                         "RingType=Metallic, SignalList=(Pristine) Pl(2), Mo(3), Pa(2), Rh(1), Se(3)",
                         "0 ly + 3 kls")

        # Verify that the default selected items after going back are what was set before selecting the child view
        validate_back(self, panel, selection_history)

        client.validate()


if __name__ == '__main__':
    unittest.main()
