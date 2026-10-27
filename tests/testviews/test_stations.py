import unittest

from testing.validation import select_item_index_and_id, validate_back, InformationPanel, assert_list_item


class StationsTestCase(unittest.TestCase):
    def setUp(self):
        self.information_panel = InformationPanel(self, "stations")


    def tearDown(self) -> None:
        self.information_panel.stop()


    def test_stations(self):
        panel = self.information_panel.panel
        view_items = self.information_panel.view_items
        client = self.information_panel.client

        selection_history = []


        station_items = select_item_index_and_id(self, self.information_panel, "Information", "Information",
                                                 1, "Stations", "Stations", None,
                                                 None, view_items, selection_history,
                                                 "Stations in Delkar|(0.0 ly from current location)", "",
                                                 footer_hint="Waiting for station information")
        item = station_items[0]
        assert_list_item(self, item, "Stations", "4", "Invergary",
                         "Coriolis Starport, Pad=L, Visited=11, Surface=N, RF RP RA OF SY MKT",
                         "533 ls")

        surface_seen = False
        last_ls_distance = None
        last_kls_distance = None

        for station_item in station_items:
            if 'Surface=Y' in station_item.sublabel:
                surface_seen = True
                last_ls_distance = None
                last_kls_distance = None
            elif surface_seen:
                self.fail("Non-surface station found after a surface station: " + str(station_item))

            if station_item.value.endswith(" ls"):
                ls_distance = int(station_item.value.replace(" ls",""))
                if last_ls_distance and last_ls_distance > ls_distance:
                    self.fail(f"Stations not sorted by distance - {ls_distance} ls was after {last_ls_distance} ls")
                if ls_distance > 999:
                    self.fail("Light-second distance greater than 999: " + str(ls_distance))
                if last_kls_distance is not None:
                    self.fail(f"Distance in kls ({last_kls_distance}) before an ls distance ({ls_distance}")
            elif station_item.value.endswith(" kls"):
                kls_distance = int(station_item.value.replace(" kls", ""))
                if last_kls_distance and last_kls_distance > kls_distance:
                    self.fail(f"Stations not sorted by distance - {kls_distance} kls was after {last_kls_distance} kls")

        validate_back(self, panel, selection_history)

        client.validate()


if __name__ == '__main__':
    unittest.main()
