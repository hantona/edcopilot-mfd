class Item:
    """An item to display in an MFD screen"""
    id_separator = "_"

    def __init__(self, view_id, item_id, drop_focus=None):
        self.view_id = view_id
        self.item_id = item_id
        self.drop_focus = drop_focus


    def as_dictionary(self) -> dict:
        """Returns a dictionary representing the entry to add to the MFD JSON file"""
        pass


    # Include the active view id in the item id added to the JSON file
    # When a select event is received, the prefix can be used to verify that the item belongs to the active view
    def get_prefixed_id(self):
        """Combines the id for the item with the view id to uniquely identify the item.

        When a select event is received, the prefix can be used to verify that the item belongs to the active view.
        There can be a mismatch if two select events are sent before the first creates a sub-menu.
        It can also occur if there are two instances of this program running at the same time.
        """
        return self.view_id + self.id_separator + self.item_id


    @staticmethod
    def split_prefixed_id(prefixed_id):

        if Item.id_separator in prefixed_id:
            return  prefixed_id.split(Item.id_separator, 1)
        else:
            raise ValueError(f"Prefixed item id did not contain the separator: {prefixed_id}")


    def __repr__(self):
        return str(self.as_dictionary())