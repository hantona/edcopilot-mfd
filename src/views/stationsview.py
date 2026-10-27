import re

from items.listitem import ListItem
from views import locationview
from baseview.dataview import DataView


class StationView(DataView):
    """Displays a list of stations in the current system

    The list is reordered so all space based stations are above all settlements and planetary outposts
    """
    def __init__(self):
        super().__init__("Stations","stations","ST",
                         display_message="Waiting for station information")


    def convert_data_to_item(self, data, index):
        data_parts = data.split("|")
        if len(data_parts) < 8:
            self.log.error(f"Station data in an unexpected format: {data}")
            return None
        item_id = data_parts[0].strip()
        station = data_parts[1]
        station_type = data_parts[2]
        distance_from_star_to_station = locationview.shorten_distance(data_parts[3].strip(), "ls")
        visited = data_parts[4].strip()
        pad = data_parts[5].strip()
        surface = data_parts[6]
        # Seen appears to be equivalent to visited > 0
        #seen = data_parts[7]
        amenities = re.sub(" +", " ", data_parts[8], count=10)


        sublabel = f"{station_type}, Pad={pad}, Visited={visited}, Surface={surface}, {amenities}"
        return  ListItem(self.view_id, item_id, station, sublabel, distance_from_star_to_station, index)


    def get_view_items(self):
        orbitals = []
        settlements = []

        for item in self.view_items:
            if 'Surface=Y' in item.sublabel:
                settlements.append(item)
            else:
                orbitals.append(item)

        orbitals.extend(settlements)

        return orbitals
