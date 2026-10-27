import re

from items.locationlistitem import LocationListItem
from baseview.dataview import DataView


def shorten_distance(distance, unit):
    """Remove commas from distances and round to ly, ls, or kls"""
    combined = ""
    prefix = ""

    if distance != "":
        distance = distance.replace(",", "")
        if float(distance) > 1000:
            prefix = "k"
            short_distance = str(round(float(distance)/1000))
        else:
            short_distance = str(round(float(distance)))

        combined = short_distance + " " + prefix + unit

    return combined


class LocationView(DataView):
    """A common view for displaying the result any of the location searches"""
    # Rename headers sent by EDCoPilot
    HEADER_MAPPING = {"PlatformSize": "Pad",
                      "SpaceOrPlanet": "Surface"}

    # Hide fields to make the view more compact
    EXCLUDE_FIELDS = {"LastUpdated"}

    def __init__(self, view_id, edcopilot_display, display_item=None, display_message=None, selling=False):
        super().__init__(view_id, edcopilot_display, "LO", item_type="LOResults", end_type="LOBlank",
                         display_item=display_item, display_message=display_message)
        self.headers = []
        self.supported_types.append("LOStructure".lower())
        self.message_handler = self.add_data
        self.destination_system = None
        self.selling = selling


    def add_data(self, data_type, data):
        if data_type == "LOStructure":
            if not self.headers:
                data_parts = data.split("|")
                for header in data_parts:
                    if not header.startswith("Spacer"):
                        # The headers can have a suffix with the recommended column width
                        if ":" in header:
                            header = re.sub(":.*", "", header)

                        if header in self.EXCLUDE_FIELDS:
                            continue

                        if header == "Quantity":
                            if self.selling:
                                header = "Demand"
                            else:
                                header = "Supply"

                        if header in self.HEADER_MAPPING:
                            self.headers.append(self.HEADER_MAPPING[header])
                        else:
                            self.headers.append(header)
        else:
            super().add_data(data_type, data)


    def convert_data_to_item(self, data, index):
        data_parts = data.split("|")

        item_id = None
        system = ""
        station = ""
        distance_to_system = None
        distance_from_star_to_station = None
        label = None
        sublabel = ""
        system_and_ring = None
        comment = ""

        for header, value in zip(self.headers, data_parts):
            if header == "NumSelector":
                item_id = value
            elif header == "SystemAndStation":
                # There can be a comment like '(-20% Cargo racks)' added on the end of SystemAndStation
                name_match = re.match("^([^(]+) \\(([^)]+)\\)( \\((.*)\\))?", value)
                if name_match:
                    system = name_match.group(1)
                    station = name_match.group(2)
                    comment = name_match.group(4)
                else:
                    self.log.warning(f"Unable to parse system and station from SystemAndStation: {value}")
            elif header == "System":
                system = value
            elif header == "Station":
                station = value
            elif header == "SystemAndRing":
                system_and_ring = value
            elif header == "StarDistance":
                distance_from_star_to_station = shorten_distance(value, "ls")
            elif header == "Distance":
                distance_to_system = shorten_distance(value, "ly")
            else:
                if sublabel == "":
                    sublabel = header + "=" + value
                else:
                    sublabel = sublabel + ", " + header + "=" + value

        if system_and_ring:
            label = system_and_ring
        if system and station:
            label = system + " - " + station

            if comment:
                label += " (" + comment + ")"
        elif system:
            label = system
        elif station:
            label = station

        if distance_to_system and distance_from_star_to_station:
            value = distance_to_system + " + " + distance_from_star_to_station
        elif distance_to_system:
            value = distance_to_system
        elif distance_from_star_to_station:
            value = distance_from_star_to_station
        else:
            value = ""

        item = LocationListItem(self.view_id, item_id, label, sublabel, value, index, system, station,
                                drop_focus=True)

        return item


    def build_items(self):
        updated = super().build_items()
        return updated


    def select_item(self, item_id):
        item = self.get_view_item(item_id)
        self.plot_route(item.system)
        return False


    def plot_route(self, destination_system):
        self.log.info(f"Plotting route to {destination_system}")
        self.client.switch_view("BookmarkButtonSelect:OnClickBookmarkLabel", destination_system)
        self.set_footer_hint(f"Plotting route to {destination_system}", 8)

