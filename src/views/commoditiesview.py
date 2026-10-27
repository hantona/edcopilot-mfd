# Commodities have custom options
# BuyOrSellCommodities -> <LCDetail>18|Bauxite|Refined
# SetCommodity:Bauxite -> <LCCommodity>Bauxite
# FindClosestBuy, FindLocalBuy, FindRecommendedBuy, FindLowestPriceBuy, FindClosestSell, ... ->
# <LOStructure>NumSelector|SystemAndStation:45|Spacer1|PlatformSize|Spacer1|SpaceOrPlanet|StarDistance|Spacer2|Distance|
#              Spacer2|Price|Spacer2|Quantity|Spacer2|LastUpdated
# <LOResults>1|WISE 0713-2917 (Umbra Saeculi)|L|N||10.44|891|170843|21 hours ago

from items.listitem import ListItem
from data import commodities
from baseview.dataview import DataView
from baseview.fixedlistview import FixedListView
from views.locationview import LocationView
from baseview.nestedsearchview import NestedSearchView

class CommoditiesView(NestedSearchView):
    """The top level Commodities view

    Contains a categorized list of commodities.
    When a commodity is selected, a menu of search options is presented (Buy vs Sell) and (Local, Closest, and Recommended)
    Selecting an option displays a list of locations for the commodity.

    The Rare category has special handling because each one is only sold in one location.
    There is a separate EDCoPilot message that requests the buy locations for all the rare commodities with no
    option selection.  The Rare category submenu makes this request directly instead of listing the rare commodities.
    """
    def __init__(self):
        super().__init__("Commodities", CommodityList(), self.commodity_detail_factory,
                         search_by_label=True, categories=commodities.commodities_categories)


    @staticmethod
    def commodity_detail_factory(search, search_label):
        if search == "* RARES *":
            # Rare commodities can only be bought and only in one place
            # Skip the transaction type picker
            return RareLocationView(search, search_label)
        else:
            return CommodityTransactionView(search, search_label)


    def select_item(self, item_id):
        # The rare commodities are already in a sub-search
        # Display the sub-search instead of a Rare category containing only '* Rares *', which would trigger the sub-search
        if self.active_view is None and self.categories and self.base_view.active_view is None and item_id == "Rare":
                # User is selecting a category
                self.selected_label = 'Rare'
                self.active_view = RareLocationView("", "")
                self.active_view.parent = self
                self.switched_view = True
                self.active_view.activate_view()
                return True
        else:
            return super().select_item(item_id)

    def get_footer_hint(self):
        return super().get_footer_hint()


class CommodityList(DataView):
    """List all commodities without categories"""
    def __init__(self):
        super().__init__("Commodity", "BuyOrSellCommodities", "LC",
                         display_message="Waiting for list of commodities")


    def convert_data_to_item(self, data, index):
        data_parts = data.split("|")

        if len(data_parts) != 3:
            self.log.error(f"Commodity list data in an unexpected format: {data}")
            return None

        item_id = data_parts[0]
        label = data_parts[1]
        return  ListItem(self.view_id, item_id, label, None, None, index)


class CommodityTransactionView(NestedSearchView):
    """Lists the commodity search options and performs the search when one is selected"""
    def __init__(self, commodity, _label):
        self.commodity = commodity
        super().__init__("Commodity Transaction", TransactionList(self.commodity),
                         CommodityLocationView)

    def back(self):
        result = super().back()

        if result:
            # Resend the select commodity command
            # Selecting a different option from the list doesn't work unless the selection is resent
            self.base_view.activate_view()
        return result


class TransactionList(FixedListView):
    """The list of search options"""
    def __init__(self, commodity):
        view_id = "Transaction List"
        self.commodity = commodity
        view_items = [
             ListItem(view_id, "FindClosestBuy", "Find Closest Buy", None, None, 1),
             ListItem(view_id, "FindLocalBuy", "Find Local Buy", None, None, 2),
             ListItem(view_id, "FindRecommendedBuy", "Find Recommended Buy", None, None, 3),
             ListItem(view_id, "FindClosestSell", "Find Closest Sell", None, None, 4),
             ListItem(view_id, "FindLocalSell", "Find Local Sell", None, None, 5),
             ListItem(view_id, "FindRecommendedSell", "Find Recommended Sell", None, None, 6)
        ]
        super().__init__(view_id, view_items)

    def activate_view(self):
        super().activate_view()
        self.client.switch_view_and_wait("SetCommodity", self.commodity)


class CommodityLocationView(LocationView):
    """A list of non-rare commodity locations"""
    def __init__(self, search, _label):
        super().__init__("Commodity Location",search, selling=search.endswith("Sell"), display_message="Waiting for commodity locations")
        self.search = search


class RareLocationView(LocationView):
    """A list of the location for all rare commodities"""
    def __init__(self, search, _label):
        super().__init__("Commodity Location","SetCommodity", "* RARES *", display_message="Waiting for rare commodity locations")
        self.search = search

        # The headers returned by EDCoPilot don't match the order of the fields it sends
        self.headers = ["NumSelector", "SystemAndStation", "Commodity", "Pad", "Surface", "StarDistance", "Distance", "Supply"]
