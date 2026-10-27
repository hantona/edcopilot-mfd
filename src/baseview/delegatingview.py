from items.item import Item
from baseview.view import View

class DelegatingView(View):
    """Base class for views that wrap one or more views and delegate most of the methods to the child view"""
    def __init__(self, view_id, child_views):
        self.child_views = child_views
        super().__init__(view_id)


    def get_delegate(self) -> View | None:
        raise NotImplementedError("get_delegate must be implemented")


    def get_child_views(self):
        return self.child_views.copy()


    def get_view_id(self):
        return self.view_id


    def can_accept_data(self, data_type):
        result = None
        delegate = self.get_delegate()
        if delegate:
            result = delegate.can_accept_data(data_type)

        return result


    def add_data(self, data_type, data):
        result = None
        delegate = self.get_delegate()
        if delegate:
            result = delegate.add_data(data_type, data)

        return result


    def convert_data_to_item(self, data, index) -> Item | None:
        result = None
        delegate = self.get_delegate()
        if delegate:
            result = delegate.convert_data_to_item(data, index)

        return result


    def build_items(self):
        result = None
        delegate = self.get_delegate()
        if delegate:
            result = delegate.build_items()

        return result


    def select_item(self, item_id):
        result = False
        delegate = self.get_delegate()
        if delegate:
            result = delegate.select_item(item_id)

        return result


    def back(self):
        result = None
        delegate = self.get_delegate()
        if delegate:
            result = delegate.back()

        return result


    def activate_view(self):
        super().activate_view()
        delegate = self.get_delegate()
        if delegate:
            delegate.activate_view()


    def deactivate_view(self):
        delegate = self.get_delegate()
        if delegate:
            delegate.deactivate_view()


    def get_title(self):
        delegate = self.get_delegate()
        if delegate:
            result = delegate.get_title()
        else:
            result = super().get_title()

        return result


    def reset_view(self):
        delegate = self.get_delegate()
        if delegate:
            delegate.reset_view()
            delegate.deactivate_view()


    def get_view_type(self):
        result = None
        delegate = self.get_delegate()
        if delegate:
            result = delegate.get_view_type()

        return result


    def get_footer_hint(self):
        delegate = self.get_delegate()
        if delegate:
            result = delegate.get_footer_hint()
        else:
            result = self.footer_hint

        return result


    def focus_lost(self):
        delegate = self.get_delegate()
        if delegate:
            delegate.focus_lost()


    def get_active_view_id(self):
        delegate = self.get_delegate()
        if delegate:
            return delegate.get_active_view_id()
        else:
            return super().get_active_view_id()


    def set_selected_item_index(self, index):
        delegate = self.get_delegate()
        if delegate:
            delegate.set_selected_item_index(index)
        else:
            self.selected_item_index = index


    def get_selected_item_index(self):
        delegate = self.get_delegate()
        if delegate:
            return delegate.get_selected_item_index()
        else:
            return self.selected_item_index
