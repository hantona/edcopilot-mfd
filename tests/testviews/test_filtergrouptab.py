import unittest

from baseview.filtergroupview import FilterGroupView
from baseview.fixedlistview import FixedListView
from items.listitem import ListItem
from testing.validation import assert_labels


class FilterGroupViewTestCase(unittest.TestCase):
    def test_group_by_id_other_exists(self):
        items = [ListItem("FIX_TAB_ID", "Platinum", "1", "", "", 1),
                 ListItem("FIX_TAB_ID", "Gallite", "2", "", "", 2),
                 ListItem("FIX_TAB_ID", "Void Opals", "3", "", "", 3),
                 ListItem("FIX_TAB_ID", "Neither", "4", "", "", 4)]
        base = FixedListView("test", items)
        groups = {
            "Core": ["Platinum", "Void Opals"],
            "Laser": ["Platinum", "Gallite"],
        }
        nested = FilterGroupView("Filtered", base, groups)
        self.assertTrue(nested.build_items())
        view_items = nested.get_view_items()
        self.assertEqual(3, len(view_items))
        self.assertEqual("Core", view_items[0].item_id)
        self.assertEqual("Laser", view_items[1].item_id)
        self.assertEqual("Other", view_items[2].item_id)

        nested.select_item("Laser")
        self.assertTrue(nested.build_items())
        view_items = nested.get_view_items()
        self.assertEqual(2, len(view_items))
        self.assertEqual("Platinum", view_items[0].item_id)
        self.assertEqual("Gallite", view_items[1].item_id)

        nested.back()
        nested.select_item("Core")
        self.assertTrue(nested.build_items())
        view_items = nested.get_view_items()
        self.assertEqual(2, len(view_items))
        self.assertEqual("Platinum", view_items[0].item_id)
        self.assertEqual("Void Opals", view_items[1].item_id)

    def test_group_by_id_no_other(self):
        items = [ListItem("FIX_TAB_ID", "Platinum", "1", "", "", 1),
                 ListItem("FIX_TAB_ID", "Gallite", "2", "", "", 2),
                 ListItem("FIX_TAB_ID", "Void Opals", "3", "", "", 3)]
        base = FixedListView("test", items)
        groups = {
            "Core": ["Platinum", "Void Opals"],
            "Laser": ["Platinum", "Gallite"],
        }
        nested = FilterGroupView("Filtered", base, groups)
        self.assertTrue(nested.build_items())
        view_items = nested.get_view_items()
        self.assertEqual(2, len(view_items))
        self.assertEqual("Core", view_items[0].item_id)
        self.assertEqual("Laser", view_items[1].item_id)


    def test_group_by_label(self):
        items = [ListItem("FIX_TAB_ID", "1", "Platinum", "", "", 1),
                 ListItem("FIX_TAB_ID", "2", "Gallite", "", "", 2),
                 ListItem("FIX_TAB_ID", "3", "Void Opals", "", "", 3),
                 ListItem("FIX_TAB_ID", "4", "Neither", "", "", 4)]
        base = FixedListView("test", items)
        groups = {
            "Core": ["Platinum", "Void Opals"],
            "Laser": ["Platinum", "Gallite"],
        }
        nested = FilterGroupView("Filtered", base, groups)
        self.assertTrue(nested.build_items())
        view_items = nested.get_view_items()
        assert_labels(self, view_items, ["Core", "Laser", "Other"])

        nested.select_item("Laser")
        self.assertTrue(nested.build_items())
        view_items = nested.get_view_items()
        assert_labels(self, view_items, ["Platinum", "Gallite"])

        nested.back()
        nested.select_item("Core")
        self.assertTrue(nested.build_items())
        view_items = nested.get_view_items()
        assert_labels(self, view_items, ["Platinum", "Void Opals"])


    def test_group_by_label_no_other(self):
        items = [ListItem("FIX_TAB_ID", "1", "Platinum", "", "", 1),
                 ListItem("FIX_TAB_ID", "2", "Gallite", "", "", 2),
                 ListItem("FIX_TAB_ID", "3", "Void Opals", "", "", 3)]
        base = FixedListView("test", items)
        groups = {
            "Core": ["Platinum", "Void Opals"],
            "Laser": ["Platinum", "Gallite"],
        }
        nested = FilterGroupView("Filtered", base, groups)
        self.assertTrue(nested.build_items())
        view_items = nested.get_view_items()
        assert_labels(self, view_items, ["Core", "Laser"])


if __name__ == '__main__':
    unittest.main()
