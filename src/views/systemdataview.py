from items.keyvalueitem import KeyValueItem
from baseview.dataview import DataView


class SystemDataView(DataView):
    """Displays attributes about the current system"""
    def __init__(self):
        super().__init__("System Data","InfoTab","SI", "keyvalue",
                         item_type="SIBASICCURRENT", display_message="Waiting for system data")


    def build_items(self):
        return True


    def get_view_items(self):
        items = []

        if self.data_list and self.data_list[0]:
            data_parts = self.data_list[0].split("|")
            if len(data_parts) < 17:
                self.log.error(f"Biologicals data in an unexpected format: {self.data_list[0]}")
                return None
            system_name = data_parts[0]
            last_visited = data_parts[1]
            visits = data_parts[2]
            population = data_parts[3]
            allegiance = data_parts[4]
            economy = data_parts[5]
            secondary_economy = data_parts[6]
            government = data_parts[7]
            security = data_parts[8]
            faction = data_parts[9]
            growth = data_parts[11]
            # unknown = data_parts[12]
            # system is and system_name are equivalent
            # system = data_parts[13]
            controlling_power = data_parts[14]
            power_state = data_parts[15]
            conflict = data_parts[16]

            if economy and secondary_economy:
                economy = economy + ", " + secondary_economy

            items = [KeyValueItem(self.view_id, "System Name", "System Name", system_name, 0),
                     KeyValueItem(self.view_id, "Last Visited", "Last Visited", last_visited, 0),
                     KeyValueItem(self.view_id, "Visits", "Visits", visits, 0),
                     KeyValueItem(self.view_id, "Population", "Population", population, 0),
                     KeyValueItem(self.view_id, "Allegiance", "Allegiance", allegiance, 0),
                     KeyValueItem(self.view_id, "Economy", "Economy", economy, 0),
                     KeyValueItem(self.view_id, "Government", "Government", government, 0),
                     KeyValueItem(self.view_id, "Security", "Security", security, 0),
                     KeyValueItem(self.view_id, "Dominant Faction", "Dominant Faction", faction, 0),
                     KeyValueItem(self.view_id, "Growth", "Growth", growth, 0),
                     KeyValueItem(self.view_id, "Controlling Power", "Controlling Power", controlling_power, 0),
                     KeyValueItem(self.view_id, "Power State", "Power State", power_state, 0),
                     KeyValueItem(self.view_id, "Conflict", "Conflict", conflict, 0)
                     ]

        return items
