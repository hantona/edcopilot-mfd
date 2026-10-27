from data.miningcategories import mining_categories

from views.locationview import LocationView
from baseview.nestedsearchview import NestedSearchView
from views.mininghotspotview import MiningList


class MiningSellView(NestedSearchView):
    """Display the best sell locations for mining elements by type (Laser, Core, and Surface)"""
    def __init__(self):
        self.mining_list = MiningList("Mining Sell List", display_message="Waiting for list of mining materials")
        super().__init__("Mining Sell", self.mining_list, MiningSellLocationView,
                         search_by_original_index=True, categories=mining_categories)


class MiningSellLocationView(LocationView):
    """Display the mining locations for one element"""
    def __init__(self, search, search_label):
        super().__init__("Mining Sell Search","SelectCoordButton", display_item=search)
        self.display_message = f"Waiting for list of locations to sell {search_label}"