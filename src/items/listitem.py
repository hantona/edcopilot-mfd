from items.item import Item

class ListItem(Item):
    """An item to add to a MFD tab of type list"""
    def __init__(self, view_id, item_id, label, sublabel, value, original_index, drop_focus=None):
        super().__init__(view_id, item_id, drop_focus=drop_focus)
        self.label = label
        self.sublabel = sublabel
        self.value = value
        self.original_index = original_index
        self.drop_focus = drop_focus

        if original_index == 0:
            raise ValueError("original_index cannot be 0")


    def as_dictionary(self):
        result = {"id": self.get_prefixed_id(), "label": self.label}

        if self.sublabel:
            result["sublabel"] = self.sublabel

        if self.value:
            result["value"] = self.value

        if self.drop_focus:
            result["dropFocus"] = True

        return result