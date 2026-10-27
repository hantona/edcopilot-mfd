from items.listitem import ListItem
from views import locationview
from baseview.dataview import DataView


class BodiesView(DataView):
    """A view that displays the planetary bodies in the current system"""
    def __init__(self):
        super().__init__("Bodies","ShowBodies:CurrentSystem","BY",
                         display_message="Waiting for list of bodies in the current system")

    def convert_data_to_item(self, data, index):
        data_parts = data.split("|")

        if len(data_parts) < 12:
            self.log.error(f"Bodies view data changed format: {data}")
            return None

        # data_parts[0] - C-DANGER, C-HIGH - these correspond to colors in the UI
        item_id = data_parts[1].strip()

        # Ignore stations in the bodies response
        if item_id == "":
            return None

        body = data_parts[2].strip()
        body_type = data_parts[3]
        # gravity = data_parts[4]
        # visits = data_parts[5]
        # data_parts[6] - A 3 char string representing the booleans D, S, and M as 'Y' or ' '
        if data_parts[7] != "-":
            distance_from_star_to_station = locationview.shorten_distance(data_parts[7].strip(), "ls")
        else:
            distance_from_star_to_station = ""
        # 8 and 9 are unknown
        signals = data_parts[10].strip()
        # 11 is unknown - R2R?

        sublabel = f"Type={body_type}, {signals}"
        return  ListItem(self.view_id, item_id, body, sublabel, distance_from_star_to_station, index)


    def get_view_items(self):
        orbitals = []
        settlements = []

        for item in self.view_items:
            if item.sublabel.startswith("Settlement"):
                settlements.append(item)
            else:
                orbitals.append(item)

        orbitals.extend(settlements)

        return orbitals
