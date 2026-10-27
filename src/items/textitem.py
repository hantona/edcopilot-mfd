from items.item import Item

class TextItem(Item):
    """An item for a tab of type text"""
    def __init__(self, view_id, text):
        super().__init__(view_id, None)
        self.text = text


    def as_dictionary(self) -> dict:
        return self.text
