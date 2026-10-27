from baseview.filteredview import FilteredView
from baseview.nestedview import NestedView

class FilterGroupView(NestedView):
    """A decorator that splits a view into categorized submenus"""
    def __init__(self, view_id, base_view, filter_groups):
        self.base_view = base_view
        self.updated = True

        known_items = set()
        views = []
        for filter_view_id in filter_groups.keys():
            filter_values = filter_groups[filter_view_id]
            child = FilteredView(filter_view_id, base_view, items_to_add=filter_values, in_filter_group=True)
            child.parent = self
            views.append(child)
            known_items = known_items | set(filter_values)

        self.other_view = FilteredView("Other", base_view, items_to_remove=list(known_items), in_filter_group=True)
        self.other_view.parent = self

        super().__init__(view_id, views)


    def back(self):
        self.updated = True
        self.view_items = []
        return super().back()


    def build_items(self):
        if not self.active_view and not self.other_view in self.views:
            self.views.append(self.other_view)

        updated = super().build_items()
        self.other_view.build_items()

        if not self.active_view and not self.other_view.get_view_items():
            self.views.remove(self.other_view)
            if self.view_items[-1].label == "Other":
                self.view_items.pop()

        updated |= self.updated

        return updated


    def get_view_items(self):
        items = super().get_view_items()
        return items


    def can_accept_data(self, data_type):
        return self.base_view.can_accept_data(data_type)


    def add_data(self, data_type, data):
        self.updated = True
        self.base_view.add_data(data_type, data)


    def activate_view(self):
        self.base_view.activate_view()


    def get_footer_hint(self):
        return self.base_view.get_footer_hint()
