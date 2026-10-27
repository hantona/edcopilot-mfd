import unittest

from testing.validation import select_item_index_and_id, validate_back, InformationPanel, assert_list_item


class BodiesTestCase(unittest.TestCase):
    def setUp(self):
        self.information_panel = InformationPanel(self, "bodies")


    def tearDown(self) -> None:
        self.information_panel.stop()


    def test_bodies(self):
        panel = self.information_panel.panel
        view_items = self.information_panel.view_items
        client = self.information_panel.client

        selection_history = []


        bodies_items = select_item_index_and_id(self, self.information_panel, "Information", "Information", 2,
                                                  "Bodies", "Bodies",
                                                  None, None, view_items, selection_history,
                                                "Bodies in Delkar", "",
                                                footer_hint="Waiting for list of bodies in the current system")
        item = bodies_items[0]
        assert_list_item(self, item,"Bodies", "1", "Delkar",
                         "Type=G (White-Yellow) Star, ", "")

        assert_list_item(self, bodies_items[1],"Bodies", "2", "Delkar 1",
                         "Type=Metal-rich body, 19 $PlanetaryMiningLocation_Name,2 Geological,17 Human",
                         "25 ls")

        validate_back(self, panel, selection_history)

        client.validate()


if __name__ == '__main__':
    unittest.main()
