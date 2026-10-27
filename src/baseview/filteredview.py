from baseview.delegatingview import DelegatingView
from baseview.view import View

class FilteredView(DelegatingView):
    """A decorator that filters out entries from the wrapped view"""
    def __init__(self, view_id, base_view, items_to_remove=None, items_to_add=None, in_filter_group=False):
        self.base_view = base_view
        super().__init__(view_id, [self.base_view])
        self.items_to_remove = items_to_remove
        self.items_to_add = items_to_add
        self.in_filter_group = in_filter_group

        if not self.items_to_remove and not self.items_to_add:
            raise ValueError("Filter needs items to add or remove")

        if self.items_to_remove and self.items_to_add:
            raise ValueError("Filter has both items to add and remove")


    def get_delegate(self) -> View | None:
        return self.base_view


    def get_view_items(self):
        filtered_items = []
        for item in self.base_view.get_view_items():
            if self.items_to_remove:
                if not (item.item_id in self.items_to_remove or item.label in self.items_to_remove):
                    filtered_items.append(item)
            else:
                if item.item_id in self.items_to_add or item.label in self.items_to_add:
                    filtered_items.append(item)

        return filtered_items


    def get_view_item(self, item_id):
        return self.base_view.get_view_item(item_id)


    def get_sub_views(self):
        parent_subtitle = self.parent.get_subtitle()
        if parent_subtitle:
            return f"{parent_subtitle} / {self.view_id}"
        else:
            return self.view_id


    def activate_view(self):
        if not self.in_filter_group:
            super().activate_view()

