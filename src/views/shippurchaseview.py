
from items.listitem import ListItem
from baseview.dataview import DataView
from baseview.nestedsearchview import NestedSearchView
from views.locationview import LocationView


# ShipPurchases -> <LSDetail>1|Adder
# SelectCoordButton:1 -> <LOStructure>NumSelector|SystemAndStation|Spacer2|PlatformSize|Spacer2|SpaceOrPlanet|Spacer2|
#                                     StarDistance|Spacer2|Distance
#                         <LOResults>1|LHS 253 (Cmdr Grubot's Headquarters)|L|N|14|0.0

class ShipPurchaseView(NestedSearchView):
    """The top level ship purchase view displaying a list of ships and the locations for each"""
    def __init__(self):
        super().__init__("Ship Purchases", ShipList(), ShipLocationView)


class ShipList(DataView):
    """Display the list of ships"""
    def __init__(self):
        super().__init__("Ship List", "ShipPurchases", "LS",
                         display_message="Waiting for ships available to purchase")

    def convert_data_to_item(self, data, index):
        data_parts = data.split("|")
        if len(data_parts) != 2:
            self.log.error(f"Ship data in an unexpected format: {data}")
            return None
        item_id = data_parts[0]
        label = data_parts[1]
        return  ListItem(self.view_id, item_id, label, None, None, index)


class ShipLocationView(LocationView):
    """Displays the list of locations for a ship"""
    def __init__(self, search, search_label):
        super().__init__("Ship Location","SelectCoordButton", display_item=search,
                         display_message="Waiting for locations offering the selected ship")
        self.search = search
        self.search_label = search_label
        self.display_message = f"Waiting for locations selling {search_label}"


