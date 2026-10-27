from baseview.view import View

class FixedListView(View):
    """A hardcoded view for action submenus with a fixed list of options"""
    def __init__(self, view_id, view_items):
        super().__init__(view_id)
        self.view_items = view_items

        self.updated = True

        self.view_items_by_id = {}
        for view_item in self.view_items:
            self.view_items_by_id[view_item.item_id] = view_item


    def build_items(self):
        updated_now = self.updated
        self.updated = False
        return updated_now


    def activate_view(self):
        super().activate_view()
        self.updated = True