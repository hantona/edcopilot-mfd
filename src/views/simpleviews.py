from views.locationview import LocationView

# Location search views that require no custom code

# GetTechBroker:Guardian -> <LOStructure>NumSelector|SystemAndStation|Spacer2|BrokerType|Spacer2|PlatformSize|Spacer2|
#                                        SpaceOrPlanet|Spacer2|StarDistance|Spacer2|Distance
#                           <LOResults>1|Fionn (Currie Enterprise)|Guardian|L|N|126|17.03
class GuardianTechView(LocationView):
    VIEW_ID = "Guardian Technology Broker"
    def __init__(self):
        super().__init__(self.VIEW_ID,"GetTechBroker:Guardian",
                         display_message="Waiting for the nearby Guardian Technology Brokers")


# GetTechBroker:Human -> <LOStructure>NumSelector|SystemAndStation|Spacer2|BrokerType|Spacer2|PlatformSize|Spacer2|
#                                     SpaceOrPlanet|Spacer2|StarDistance|Spacer2|Distance
#                        <LOResults>1|LP 847-48 (Rozhdestvensky Hub)|Human|L|N|7|12.60
# BookmarkButtonSelect:OnClickBookmarkLabel:LP 847-48
class HumanTechView(LocationView):
    VIEW_ID = "Human Technology Broker"
    def __init__(self):
        super().__init__(self.VIEW_ID,"GetTechBroker:Human",
                         display_message="Waiting for the nearby Human Technology Brokers")


# BestLocalRepair -> #2:<LOStructure>NumSelector|System|Spacer2|Station|Spacer2|PlatformSize|Spacer2|SpaceOrPlanet|
#                                    Spacer2|StarDistance|Spacer2|Distance
#                    #2:<LOResults>1|LHS 253|Cmdr Grubot's Headquarters|L|N|14|0.0
class RepairView(LocationView):
    def __init__(self):
        super().__init__("Repair","BestLocalRepair",
                         display_message="Waiting for the nearby locations offering repair services")


class RawMaterialsView(LocationView):
    def __init__(self):
        super().__init__("Raw Materials Trader", "GetRawMaterialTrader:",
                         display_message="Waiting for the nearby Raw material Traders")


# GetBlackMarket -> <LOStructure>NumSelector|System|Spacer2|Station|Spacer2|PlatformSize|Spacer2|SpaceOrPlanet|Spacer2|
#                                StarDistance|Spacer2|Distance
#                   <LOResults>1|WISE 0713-2917|[SCCV] Starke Governor (JNB-21H)|L|N||10.44
class BlackMarketView(LocationView):
    def __init__(self):
        super().__init__("Black Market","GetBlackMarket")


class EncodedMaterialView(LocationView):
    def __init__(self):
        super().__init__("Encoded Materials Trader","GetEncodedMaterialTrader",
                         display_message="Waiting for the nearby Encoded material Traders")


class ManufacturedMaterialsView(LocationView):
    def __init__(self):
        super().__init__("Manufactured Materials Trader","GetManufacturedMaterialTrader",
                         display_message="Waiting for the nearby Manufactured material Traders")