from items.item import Item

class KeyValueItem(Item):
    """An item to add to a MFD tab of type keyvalue"""
    def __init__(self, view_id, item_id, key, value, original_index):
        super().__init__(view_id, item_id)
        self.key = key
        self.value = value
        self.original_index = original_index


    def as_dictionary(self):
        return {"id": self.get_prefixed_id(), "key": self.key, "value": self.value}
