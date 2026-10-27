import unittest

from testing.validation import select_item_index_and_id, assert_labels, validate_back, PlacesPanel, assert_list_item

class OutfittingTestCase(unittest.TestCase):
    def setUp(self):
        self.places_panel = None


    def tearDown(self) -> None:
        self.places_panel.stop()


    def test_outfitting(self):
        self.places_panel = PlacesPanel(self, "outfitting")
        panel = self.places_panel.panel
        view_items = self.places_panel.view_items

        selection_history = []

        title = "Outfitting"
        category_items = select_item_index_and_id(self, self.places_panel, "Places", "Places", 5,
                                                  title, title,
                                                  None, None, view_items, selection_history, title, "", footer_hint="Waiting for list of outfitting parts")
        assert_labels(self, category_items,
                      ["Hardpoint", "Utility Mount", "Optional Internal", "Core Internal", "Armour",
                       "Personal Equipment"])

        parts_items = select_item_index_and_id(self, self.places_panel, "Places", "Outfitting Parts Categories",
                                               1, "Utility Mount", "Utility Mount",
                                               None, None, category_items, selection_history, title, "Utility Mount")
        assert_list_item(self, parts_items[0], "Outfitting Parts", "13", "Caustic Sink Launcher", None, None)

        quality_items = select_item_index_and_id(self, self.places_panel, "Places", "Outfitting Parts",
                                                 3, "33", "Frame Shift Wake Scanner", None,
                                                 None, parts_items, selection_history,
                                                 title, "Utility Mount / Frame Shift Wake Scanner",
                                                 footer_hint="Waiting for available Frame Shift Wake Scanner information",
                                                 original_index=33)

        assert_labels(self, quality_items, ['0 Alpha', '0 Bravo', '0 Charlie', '0 Delta', '0 Echo'])
        self.assertEqual("1,097,100 Cr", quality_items[0].value)

        location_items = select_item_index_and_id(self, self.places_panel, "Places", "Outfitting Quality", 3,
                                                  "4", '0 Delta', None, "40,630 Cr",
                                                  quality_items, selection_history, title, "Utility Mount / Frame Shift Wake Scanner",
                                                  footer_hint="Waiting for locations selling Frame Shift Wake Scanner 0 Delta")
        location = location_items[0]
        assert_list_item(self, location, "Outfitting Location", "1",
                         "Chonti - Hadid Vision", "Pad=L, Surface=N",
                         "19 ly + 24 ls")

        # Verify that the default selected items after going back are what was set before selecting the child view
        validate_back(self, panel, selection_history)

        self.places_panel.client.validate()


    # Verify the price and that the navigation that skips the quality screen works
    def test_outfitting_armor(self):
        self.places_panel = PlacesPanel(self, "outfitting_armor")
        panel = self.places_panel.panel
        view_items = self.places_panel.view_items
        title = "Outfitting"

        selection_history = []

        category_items = select_item_index_and_id(self, self.places_panel, "Places", "Places", 5,
                                                       "Outfitting", "Outfitting",
                                                       None, None, view_items, selection_history,
                                                        title, "",
                                                  footer_hint="Waiting for list of outfitting parts")
        assert_labels(self, category_items,
                      ["Hardpoint", "Utility Mount", "Optional Internal", "Core Internal", "Armour",
                       "Personal Equipment"])

        parts_items = select_item_index_and_id(self, self.places_panel, "Places", "Outfitting Parts Categories",
                                               4, "Armour", "Armour",
                                               None, None, category_items, selection_history,
                                               title, "Armour")

        location_items = select_item_index_and_id(self, self.places_panel, "Places", "Outfitting Parts",
                                                  1, "56", "Military Grade Composite",
                                                  None, None, parts_items, selection_history, title,
                                                  "Armour / Military Grade Composite / 80,320 Cr", original_index=56,
                                                  footer_hint="Waiting for available Military Grade Composite information")
        location = location_items[0]
        assert_list_item(self, location, "Outfitting Location", "1", "Chonti - Hadid Vision", "Pad=L, Surface=N", "19 ly + 24 ls")

        # Verify that the default selected items after going back are what was set before selecting the child view
        validate_back(self, panel, selection_history)

        self.places_panel.client.validate()


if __name__ == '__main__':
    unittest.main()
