from views.biologicals import BiologicalsView
from views.bodiesview import BodiesView
from views.miningsellview import MiningSellView
from views.mininghotspotview import MiningHotspotView
from baseview.nestedview import NestedView
from views.stationsview import StationView
from views.systemdataview import SystemDataView


class InformationView(NestedView):
    """The top level information tab"""
    def __init__(self, system_name_listener):
        information_views = [SystemDataView(),
                             StationView(),
                             BodiesView(),
                             BiologicalsView(system_name_listener),
                             MiningHotspotView(),
                             MiningSellView()
                             ]

        super().__init__("Information", information_views, include_view_in_subtitle=False)
        self.system_name_listener = system_name_listener

