from baseview.delegatingview import DelegatingView
from baseview.filtergroupview import FilterGroupView
from baseview.view import View


class NestedSearchView(DelegatingView):
    """A parent class for creating a view that creates a child view to show search results based on the selected item"""
    def __init__(self, view_id, base_view, child_view_class, *, items_to_remove=None,
                 items_to_add=None, search_by_label=False, search_by_original_index=False, categories=None):
        if categories:
            self.base_view = FilterGroupView(base_view.get_view_id() + " Categories", base_view, categories)
        else:
            self.base_view = base_view
        super().__init__(view_id, [self.base_view])
        self.child_view_class = child_view_class
        self.items_to_add = items_to_add
        self.items_to_remove = items_to_remove
        self.search_by_item_id = not search_by_label and not search_by_original_index
        self.search_by_label = search_by_label
        self.search_by_original_index = search_by_original_index
        self.categories = categories

        self.active_view: View | None = None
        self.switched_view = False
        self.selected_category = None
        self.selected_label = None

        # Set the base view client after the superclass initializes it
        self.base_view.client = self.client


    def get_delegate(self) -> View | None:
        return self.active_view or self.base_view

    def get_view_items(self):
        if self.active_view:
            return self.active_view.get_view_items()
        else:
            if self.items_to_add:
                return self.filtered()
            else:
                return self.base_view.get_view_items()


    def filtered(self):
        filtered_items = []
        for item in self.base_view.get_view_items():
            if self.items_to_remove:
                if not item.item_id in self.items_to_remove:
                    filtered_items.append(item)
            else:
                if item.item_id in self.items_to_add:
                    filtered_items.append(item)

        return filtered_items


    def select_item(self, item_id):
        if self.active_view is not None:
            self.log.debug("Sending select item for "+ item_id + " to child view")
            return self.active_view.select_item(item_id)
        else:
            if self.categories and self.base_view.active_view is None:
                # User is selecting a category
                self.log.debug(f"Selecting item category {item_id} in {self.view_id}")
                self.selected_category = item_id
                return self.base_view.select_item(item_id)
            else:
                item = self.base_view.get_view_item(item_id)
                self.log.debug(f"Creating child view for {item} in {self.view_id}")
                search = None
                if self.search_by_item_id:
                    search = item.item_id
                elif self.search_by_label:
                    search = item.label
                elif self.search_by_original_index:
                    search = str(item.original_index)
                self.selected_label = item.label
                self.active_view = self.child_view_class(search, item.label)
                if self.active_view is None:
                    raise Exception("Child view creation returned None")
                self.active_view.parent = self
                self.switched_view = True
                self.active_view.activate_view()
                return True


    def back(self):
        if self.active_view is not None:
            if not self.active_view.back():
                self.active_view.deactivate_view()
                self.active_view = None
            self.switched_view = True
            back_handled = True
        else:
            back_handled = self.base_view.back()
        return back_handled


    def reset_view(self):
        if self.active_view:
            self.active_view.reset_view()
            self.active_view.deactivate_view()

        self.base_view.reset_view()
        self.base_view.deactivate_view()

        self.active_view = None
        self.switched_view = True


    def build_items(self):
        updated = super().build_items()
        if self.switched_view:
            updated = True
            self.switched_view = False

        return updated


    def get_subtitle_list(self):
        subtitle_list = []

        if self.active_view:
            if self.selected_category:
                subtitle_list.append(self.selected_category)
            subtitle_list.append(self.selected_label)
            subtitle_list.extend(self.active_view.get_subtitle_list())
        elif self.categories and self.base_view.active_view is not None:
            subtitle_list.append(self.selected_category)
            subtitle_list.extend(self.base_view.active_view.get_subtitle_list())
        elif self.base_view:
            subtitle_list.extend(self.base_view.get_subtitle_list())

        return subtitle_list


    def get_title(self):
        return self.view_id


    def activate_view(self):
        self.base_view.activate_view()
        if self.active_view:
            self.active_view.activate_view()
