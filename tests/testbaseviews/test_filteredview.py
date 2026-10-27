import unittest

from baseview.filteredview import FilteredView
from baseview.fixedlistview import FixedListView

from items.listitem import ListItem


class FilteredViewTestCase(unittest.TestCase):
    def test_view_filtering(self):
        items = [ListItem("FIX_TAB_ID", "item1", "1", "", "", 1),
                 ListItem("FIX_TAB_ID", "item2", "2", "", "", 2),
                 ListItem("FIX_TAB_ID", "item3", "3", "", "", 3),
                 ListItem("FIX_TAB_ID", "item4", "4", "", "", 4)]
        base = FixedListView("test", items)
        filtered = FilteredView("test", base, ["item1", "item3"])
        filtered_items = filtered.get_view_items()
        self.assertEqual(2, len(filtered_items))
        self.assertEqual("item2", filtered_items[0].item_id)
        self.assertEqual("item4", filtered_items[1].item_id)


if __name__ == '__main__':
    unittest.main()
