from views.simpleviews import BlackMarketView
from views.commoditiesview import CommoditiesView
from baseview.nestedview import NestedView
from views.outfittingview import OutfittingView
from views.simpleviews import RawMaterialsView
from views.simpleviews import RepairView
from views.shippurchaseview import ShipPurchaseView
from views.simpleviews import GuardianTechView, HumanTechView
from views.simpleviews import EncodedMaterialView, ManufacturedMaterialsView
from views.interstellarfactors import InterstellarFactorsView


class PlacesView(NestedView):
    def __init__(self, journal_watcher, spansh_systems):
        places_views = [
            InterstellarFactorsView(spansh_systems, journal_watcher),
            RawMaterialsView(),
            EncodedMaterialView(),
            ManufacturedMaterialsView(),
            CommoditiesView(),
            OutfittingView(journal_watcher),
            ShipPurchaseView(),
            RepairView(),
            BlackMarketView(),
            GuardianTechView(),
            HumanTechView()
        ]

        super().__init__("Places", places_views, include_view_in_subtitle=False)
        self.message_handler = self.add_data

        self.location_search_ack = False

    def activate_view(self):
        client = self.get_client()
        # Some of the location searches are broken if they are sent without a locationsearch message
        self.log.debug("Sending location search for Places view")
        client.switch_view("locationsearch", callback=self.location_search_callback)
        super().activate_view()


    def select_item(self, item_id):
        if self.location_search_ack:
            return super().select_item(item_id)
        else:
            self.log.error("Skipping Places selection because no location search ack was received")
            client = self.get_client()
            client.switch_view("locationsearch", callback=self.location_search_callback)
            return False

    def back(self):
        old_active = self.active_view
        back_handled = super().back()
        if old_active and back_handled and not self.active_view:
            client = self.get_client()
            self.location_search_ack = False
            client.switch_view("locationsearch", callback=self.location_search_callback)

        return back_handled


    def location_search_callback(self):
        self.log.debug("Location search response received")
        self.location_search_ack = True