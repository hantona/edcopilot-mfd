import unittest

from testing.validation import select_item_index_and_id, validate_back, InformationPanel, assert_list_item, PlacesPanel


class InterstellarFactorsTestCase(unittest.TestCase):
    def setUp(self):
        self.places_panel = None


    def tearDown(self) -> None:
        self.places_panel.stop()


    def test_interstellar_factors(self):
        self.places_panel = PlacesPanel(self, "interstellar_factors")
        panel = self.places_panel.panel
        view_items = self.places_panel.view_items
        client = self.places_panel.client

        selection_history = []


        station_items = select_item_index_and_id(self, self.places_panel, "Places", "Places",
                                                 0, "Interstellar Factors", "Interstellar Factors", None,
                                                 None, view_items, selection_history,
                                                 "Interstellar Factors", "",
                                                 footer_hint="Waiting for the nearby Interstellar Factors")
        item = station_items[0]
        assert_list_item(self, item, "Interstellar Factors", "1", "Crucis Sector HM-V b2-5 - Heinlein Beacon",
                         "Pad=M, Surface=N, Wanted=N",
                         "10 ly + 5 ls")

        item = station_items[1]
        assert_list_item(self, item, "Interstellar Factors", "2", "Delkar - Chapman Munitions Outpost",
                         "Pad=M, Surface=Y, Wanted=N",
                         "0 ly + 4 kls")

        validate_back(self, panel, selection_history)

        client.validate()


    def test_interstellar_factors_wanted(self):
        self.places_panel = PlacesPanel(self, "interstellar_factors")
        panel = self.places_panel.panel
        view_items = self.places_panel.view_items
        client = self.places_panel.client

        selection_history = []

        # If one of Delkar's factions is in the journal watcher's faction list, the Delkar item is marked as wanted
        self.places_panel.journal_watcher.wanted_factions = ['Movement for Delkar Revolutionary Party']


        station_items = select_item_index_and_id(self, self.places_panel, "Places", "Places",
                                                 0, "Interstellar Factors", "Interstellar Factors", None,
                                                 None, view_items, selection_history,
                                                 "Interstellar Factors", "",
                                                 footer_hint="Waiting for the nearby Interstellar Factors")
        item = station_items[0]
        assert_list_item(self, item, "Interstellar Factors", "1", "Crucis Sector HM-V b2-5 - Heinlein Beacon",
                         "Pad=M, Surface=N, Wanted=N",
                         "10 ly + 5 ls")

        item = station_items[1]
        assert_list_item(self, item, "Interstellar Factors", "2", "Delkar - Chapman Munitions Outpost",
                         "Pad=M, Surface=Y, Wanted=Y",
                         "0 ly + 4 kls")

        validate_back(self, panel, selection_history)

        client.validate()


if __name__ == '__main__':
    unittest.main()
