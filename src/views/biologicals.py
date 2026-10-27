import time

from items.keyvalueitem import KeyValueItem
from items.listitem import ListItem
from baseview.dataview import DataView
from baseview.nestedsearchview import NestedSearchView

class BiologicalsView(NestedSearchView):
    """Top level view for known biological

    Contains a view to list the known samples and a guidance view to display when a sample is selected."""
    def __init__(self, system_name_listener):
        super().__init__("Biologicals", BiologicalsListView(system_name_listener),
                         GuidanceView)


class BiologicalsListView(DataView):
    def __init__(self, system_name_listener):
        super().__init__("Biologicals", "ExoDisplay:", "EX", item_type="EXBODYDTL",
                         display_message="Waiting for known biological signals")
        self.system_name_listener = system_name_listener

    def convert_data_to_item(self, data, index):
        system_name = self.system_name_listener.get_system_name()
        data_parts = data.split("|")

        if len(data_parts) < 5:
            self.log.error(f"Biologicals data in an unexpected format: {data}")
            return None

        item_id = system_name + f"|{data_parts[0]}|{data_parts[1]}"
        label = data_parts[0] + " - " + data_parts[1]
        value = data_parts[2]
        sublabel =  f"Scanned CR={data_parts[3]},HIST={data_parts[4]}"
        return  ListItem(self.view_id, item_id, label, sublabel, value, index)


class GuidanceView(DataView):
    """View for known biological sample guidance"""
    def __init__(self, biologicals_id, _label):
        super().__init__("Guidance", "ExoNearestCoords", "GC","keyvalue", display_item=biologicals_id)

    def convert_data_to_item(self, data, index):
        split = data.split("|")
        item_id = split[0]
        key = f"Bearing: {split[0]}"
        value = f"Distance: {split[1]}"
        return KeyValueItem(self.view_id, item_id, key, value, index)


    def activate_view(self):
        super().activate_view()
        # The ExoNearestCoords doesn't return a response message when it has been processed
        # Sending a guidance message immediately will cancel the ExoNearestCoords message
        time.sleep(5)
        self.client.switch_view("guidance")
