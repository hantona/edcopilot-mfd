from baseview.delegatingview import DelegatingView
from items.listitem import ListItem
from baseview.view import View


class NestedView(DelegatingView):
    """A view that displays a menu of sub-views"""
    def __init__(self, view_id, views, *, include_view_in_subtitle=True):
        self.views: list[View] = views
        super().__init__(view_id, views)
        self.active_view = None
        self.switched_view = False
        self.include_view_in_subtitle = include_view_in_subtitle


    def get_delegate(self):
        if self.active_view:
            return self.active_view
        else:
            return None


    def build_items(self):
        updated = False
        active_view = self.active_view

        if active_view:
            updated = active_view.build_items()
            if updated or self.switched_view:
                self.view_items.clear()
                self.view_items.extend(active_view.get_view_items())
        else:
            if self.switched_view or not self.view_items:
                updated = True
                self.view_items.clear()
                index = 1
                for view in self.views:
                    self.view_items.append(ListItem(self.view_id, view.view_id, view.view_id, None,
                                                    None, index))
                    index += 1

        if self.switched_view:
            updated = True
            self.switched_view = False

        return updated


    def activate_view(self):
        super().activate_view()
        if self.active_view:
            self.active_view.activate_view()


    def select_item(self, item_id):
        result = False
        if self.active_view is not None:
            result = self.active_view.select_item(item_id)
        else:
            for view in self.views:
                if view.view_id == item_id:
                    self.active_view = view
                    self.switched_view = True
                    self.active_view.selected_item_index = 0
                    self.active_view.activate_view()
                    result = True
                    break
        return result


    def back(self):
        back_handled = False

        if self.active_view:
            if not self.active_view.back():
                self.active_view.deactivate_view()
                self.active_view = None
            self.switched_view = True
            back_handled = True

        return back_handled


    def get_subtitle_list(self):
        subtitle_list = []

        if self.active_view:
            if self.include_view_in_subtitle:
                subtitle_list.append(self.active_view.view_id)
            subtitle_list.extend(self.active_view.get_subtitle_list())

        return subtitle_list


    def get_subtitle_parts(self):
        if self.active_view and self.include_view_in_subtitle:
            return [self.active_view.view_id]
        else:
            return []


    def reset_view(self):
        if self.active_view:
            self.active_view.reset_view()
            self.active_view.deactivate_view()

        self.active_view = None
        self.switched_view = True


    def get_view_item(self, item_id):
        if self.active_view:
            return self.active_view.get_view_item(item_id)
        else:
            return None

    def get_view_type(self):
        # If the child view isn't active, a list of child views is shown
        return super().get_view_type() or "list"


