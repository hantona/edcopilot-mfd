from baseview.dataview import DataView
from baseview.nestedsearchview import NestedSearchView
from data.hotspots import hotspots
from items.listitem import ListItem
from views.locationview import LocationView


class MiningHotspotView(NestedSearchView):
    """Display a list of the mining elements that have hotspots and the locations for each"""
    def __init__(self):
        view_id = "Mining Hotspots"
        super().__init__(view_id, MiningList("Mining Hotspots List",
                                            display_message="Waiting for list of mining hotspot materials"),
                         MiningHotspotLocationView, items_to_add=hotspots)

    def get_title(self):
        return self.view_id


class MiningList(DataView):
    """List the mining elements sorted by price without categorization or filtering"""
    def __init__(self, view_id, display_message):
        super().__init__(view_id, "GetBestMiningPrices", "MP", display_message=display_message)


    def convert_data_to_item(self, data, index):
        data_parts = data.split("|")
        if len(data_parts) < 2:
            self.log.error(f"Mining prices data in an unexpected format: {data}")
            return None
        item_id = data_parts[0]
        label = data_parts[0]
        value = data_parts[1]
        return  ListItem(self.view_id, item_id, label, None, value, index)


    def build_items(self):
        updated = super().build_items()
        # Sort items in descending order by price
        self.view_items = sorted(self.view_items, key=lambda item: int(item.value.replace(",", "")), reverse=True)
        return updated


class MiningHotspotLocationView(LocationView):
    """Display nearby hotspot locations for a single element"""
    def __init__(self, search, search_label):
        super().__init__("Mining Search","FindSignalsAndHotspots",
                         display_item=search)
        self.display_message = f"Waiting for nearby {search_label} hotspots"

        # The hotspot headers sent by EDCoPilot don't match the order of the data it sends
        self.headers = ['NumSelector', 'SystemAndRing', 'RingType', 'SignalList', 'StarDistance', 'Distance']
