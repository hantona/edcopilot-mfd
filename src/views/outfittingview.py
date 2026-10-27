import pricelookup
from baseview.delegatingview import DelegatingView
from baseview.view import View
from data.outfittingcategories import outfitting_categories
from items.listitem import ListItem
from baseview.dataview import DataView
from baseview.nestedsearchview import NestedSearchView
from views.locationview import LocationView





# Outfitting -> <LMDetail>89|Prismatic Shield Generator
# Outfitting:Prismatic Shield Generator  -> <LTDetail>1~1 Alpha
# <switchTo:#2:SelectCoordButton:1:endSwitch> ->
#       <LOStructure>NumSelector|SystemAndStation|Spacer2|PlatformSize|Spacer2|
#                    SpaceOrPlanet|Spacer2|StarDistance|Spacer2|Distance
#       <LOResults>1|Gendalla (Clervoy City) (-20% Cargo racks, Hull reinforcements discount)|L|N|91|17.52
# <switchTo:BookmarkButtonSelect:OnClickBookmarkLabel:Gendalla:endSwitch>

class OutfittingView(NestedSearchView):
    """The top level outfitting view"""
    def __init__(self, journal_watcher):
        super().__init__("Outfitting", OutfittingPartsList(), self.outfitting_quality_or_location_factory,
                         search_by_label=True,categories=outfitting_categories)
        self.journal_watcher = journal_watcher

    def outfitting_quality_or_location_factory(self, part_name, search_label):
        return OutfittingQualityOrLocation(self.journal_watcher, part_name, search_label)


class OutfittingPartsList(DataView):
    def __init__(self):
        super().__init__("Outfitting Parts", "ShipOutfitting", "LM",
                         display_message="Waiting for list of outfitting parts")

    def convert_data_to_item(self, data, index):
        data_parts = data.split("|")
        if len(data_parts) != 2:
            self.log.error(f"Outfitting parts data was in an unexpected format: {data}")
            return None
        item_id = data_parts[0]
        label = data_parts[1]
        return  ListItem(self.view_id, item_id, label, None, None, index)


class OutfittingQualityOrLocation(DelegatingView):
    """Display an item quality selector or a list of locations based on the data received

    An outfitting query for a specific part usually returns a list of grades to choose from.
    If there is only one grade for an item, the locations are returned instead.
    """
    def __init__(self, journal_watcher, part_name, search_label):
        self.journal_watcher = journal_watcher
        self.part_name = part_name
        self.search_label = search_label
        self.quality = OutfittingQualityView(self.journal_watcher, self.part_name, self.search_label)
        self.location = OutfittingLocationView(self.part_name, "", "")
        super().__init__("OutfittingQualityOrLocation", [self.quality, self.location])

        self.quality_data_seen = False
        self.location_data_seen = False


    def get_delegate(self) -> View:
        # The view will initially behave like a quality view.
        # If the item search query returns location information instead of a list of qualities for the item, use the location view to display the data.
        if self.location_data_seen:
            return self.location
        else:
            return self.quality


    def add_data(self, data_type, data):
        if self.quality.can_accept_data(data_type):
            self.quality_data_seen = True
        if not self.quality_data_seen and self.location.can_accept_data(data_type):
            self.location_data_seen = True
        super().add_data(data_type, data)


    def can_accept_data(self, data_type):
        return self.quality.can_accept_data(data_type) or self.location.can_accept_data(data_type)


    def get_view_items(self):
        delegate = self.get_delegate()
        return delegate.get_view_items()


    def get_subtitle_list(self):
        ship_type = self.journal_watcher.get_ship_type()
        price = pricelookup.find_price(self.part_name, self.search_label, ship_type)
        if price:
            return [price]
        else:
            return []


class OutfittingQualityView(NestedSearchView):
    """Display available qualities for an item and the locations when a quality is selected"""
    def __init__(self, journal_watcher, part_name, _search_label):
        self.part_name = part_name
        super().__init__("Outfitting Quality", OutfittingQualityList(journal_watcher, self.part_name),
                        self.location_factory)

    def location_factory(self, search, search_label):
        return OutfittingLocationView(self.part_name, search, search_label)


class OutfittingQualityList(DataView):
    """Display a list of qualities that an item is available in"""
    def __init__(self, journal_watcher, part_name):
        super().__init__("Outfitting Quality", "Outfitting", "LT", display_item=(part_name + "~"))
        self.journal_watcher = journal_watcher
        self.display_message = f"Waiting for available {part_name} information"
        self.part_name = part_name

    def convert_data_to_item(self, data, index):
        data_parts = data.split("~")
        if len(data_parts) != 2:
            self.log.error(f"Outfitting quality data in an unexpected format: {data}")
            return None
        item_id = data_parts[0]
        label = data_parts[1]

        ship_type = self.journal_watcher.get_ship_type()
        value = pricelookup.find_price(self.part_name, label, ship_type)

        return  ListItem(self.view_id, item_id, label, None, value, index)


class OutfittingLocationView(LocationView):
    def __init__(self, part_name, quality_list_index, quality_label):
        super().__init__("Outfitting Location","SelectCoordButton", quality_list_index,
                         f"Waiting for locations selling {part_name} {quality_label}")

