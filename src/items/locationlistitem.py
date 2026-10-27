from items.listitem import ListItem

class LocationListItem(ListItem):
    """A list item that stores the system and station to simplify handling select events on locations"""
    def __init__(self, view_id, item_id, label, sublabel, value, original_index, system, station, drop_focus=None):
        super().__init__(view_id, item_id, label, sublabel, value, original_index, drop_focus=drop_focus)
        self.system = system
        self.station = station