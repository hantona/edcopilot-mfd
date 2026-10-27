import logging
import time

from items.item import Item


class View:
    """The base class for views included in an MFD tab"""
    def __init__(self, view_id, view_type="list"):
        self.view_id = view_id
        self.view_type = view_type
        self.title = view_id
        self.subtitle = ""
        self.client = None
        self.parent = None
        self.footer_hint = None
        self.footer_expiration = None

        self.view_items = []
        self.view_items_by_id = {}
        self.data_list = None
        self.selected_item_index = 0

        for view in self.get_child_views():
            view.parent = self

        self.log = logging.getLogger(self.__class__.__name__)


    def get_view_id(self):
        """Get the id of the view

        Each nested view in tab has a distinct id, which is used as a prefix for all of the item ids"""
        return self.view_id


    def get_view_items(self):
        """Returns the list of Item objects to display in the view"""
        return self.view_items.copy()


    def can_accept_data(self, data_type):
        """Returns true if the view can process the data type prefix from the EDCoPilot message"""
        return False


    def add_data(self, data_type, data):
        """Adds data from an EDCoPilot message to the view

        This is only called if can_accept data returned true for the data_type.
        The data will later be passed to convert_data_to_item to create the Item object to display.
        """
        pass


    def convert_data_to_item(self, data, index) -> Item | None:
        """Builds an Item object corresponding to the view type from the MFD Spec.
        data -- the contents of the EDCopilot message
        index -- a 1-based index of the data in the list received from EDCoPilot

        Some follow-on messages that need to be sent to navigate to a sub-menu need to include the index even
        though it isn't explicitly included in the data from the parent view.  If a view applies sorting to the
        Item list, the items will no longer be in the same order, so the index needs to be stored in the Item's
        original_index attribute.

        A view of type 'list' produces ListItem objects, a 'keyvalue' view produces KeyValueItem objects and a 'text'
        view produces TextItem objects.
        """
        return None


    def build_items(self):
        """Builds the list of Items for the view to display

            Returns true if the content of the view has changed since the last call to build_items.
        """
        return False


    def select_item(self, item_id):
        """Processes a user selecting an Item

        Returns True if the selection created a sub-menu view to allow the active selection to be restored later when the user presses back.

        Implementations usually create a child view or send an EDCoPilot message on Item selection.
        """
        return False


    def back(self):
        """Handles the user pressing the back button while the view is active"""
        self.selected_item_index = 0
        return False


    def activate_view(self):
        """Called when the view is created

        This method usually sends an EDCoPilot message requesting data to populate the view.
        """
        self.client = self.get_client()


    def deactivate_view(self):
        pass


    def get_client(self):
        """Gets the socket client to use for sending EDCoPilot messages related to the view

        The socket client is shared between all views in a top level tab.
        """
        if self.client is not None:
            client = self.client
        elif self.parent is not None:
            client = self.parent.get_client()
            if client is None:
                raise ValueError(f"Parent client was None for view {self.view_id}")
        else:
            raise ValueError(f"View {self.view_id} has no parent and no message handler")

        return client


    def get_title(self):
        """Gets the title to use for the MFD tab while the view is active"""
        return self.title


    def get_subtitle_list(self):
        """Gets a list of subtitle elements to display for the view and its active child views"""
        return []


    def get_subtitle(self):
        """Gets the subtitle to used as the MFD tab subtitle while the view is active

        The subtitle usually includes a list of values matching the child view navigation path to the active view"""
        subtitles =  self.get_subtitle_list()

        if not subtitles:
            return ""
        else:
            return " / ".join(subtitles)


    def reset_view(self):
        """Clear all view data on a connection loss"""
        self.data_list = None
        self.view_items.clear()


    def get_view_item(self, item_id):
        """Returns the Item in the view with the given item_id attribute"""
        try:
            return self.view_items_by_id[item_id]
        except KeyError as e:
            self.log.error(f"View item with id {item_id} does not exist: {self.view_items_by_id.keys()}")
            raise e


    def get_view_type(self):
        """Gets the type of the view to be used as the MFD tab type while the view is active"""
        return self.view_type


    def get_child_views(self):
        """Get the child views of the view to allow automatically setting each view's parent view"""
        return []


    def set_footer_hint(self, footer_hint, expiration):
        """Sets the footer hint to display at the bottom of the MFD tab when the view is active

        expiration -- if not None, the number of seconds to display the message for
        """
        self.footer_hint = footer_hint
        if footer_hint is not None:
            self.log.info(f"Adding footer_hint {footer_hint}")

        if expiration is not None:
            self.footer_expiration = time.time() + expiration
        else:
            self.footer_expiration = None


    def get_footer_hint(self):
        """Returns the footer hint if one was set and has not expired"""
        if self.footer_expiration is None or time.time() < self.footer_expiration:
            return self.footer_hint
        else:
            return ""


    def focus_lost(self):
        """Called when the user switches away from the view"""
        pass


    def get_active_view_id(self):
        """Gets the view id for this view or its active child view"""
        return self.view_id


    def set_selected_item_index(self, index):
        """Sets the index of the highlighted item in the MFD tab"""
        self.selected_item_index = index


    def get_selected_item_index(self):
        """Get the stored index of the highlighted item in the MFD tab"""
        return self.selected_item_index


    @staticmethod
    def needs_client():
        """Returns True if the view uses a client to send messages

        Views that only process incoming broadcast messages should return false
        """
        return True


    def __repr__(self):
        return f"View: {self.view_id} Type: {type(self).__name__}"
