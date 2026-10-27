from baseview.view import View


class DataView(View):
    """A view driven directly by data from EDCopilot"""
    def __init__(self, view_id, edcopilot_display, data_prefix, view_type="list", *,
                 display_item=None, start_type=None, item_type=None, end_type=None,
                 display_message=""):
        super().__init__(view_id, view_type)
        self.edcopilot_display = edcopilot_display
        self.title_type = data_prefix + "Title"
        self.start_type = start_type or data_prefix + "Clear"
        self.item_type = item_type or data_prefix + "Detail"
        self.end_type = end_type or data_prefix + "Display"
        self.display_item = display_item
        self.display_message = display_message
        self.data_added = False

        # lower case versions of the data types the view supports
        self.supported_types = [self.title_type.lower()]

        if self.start_type:
            self.supported_types.append(self.start_type.lower())

        if self.item_type:
            self.supported_types.append(self.item_type.lower())

        if self.end_type:
            self.supported_types.append(self.end_type.lower())


    def can_accept_data(self, data_type):
        return data_type.lower() in self.supported_types


    def add_data(self, data_type, data):
        if not self.data_list:
            self.data_list = []

        if data_type == self.item_type:
            self.data_list.append(data)
            self.footer_hint = None
            self.footer_expiration = None
        elif data_type == self.title_type:
            self.title = data
            self.subtitle = data
        self.data_added = True


    def build_items(self):
        updated = self.data_added

        if self.data_list:
            updated = True
            self.view_items.clear()
            self.view_items_by_id.clear()
            index = 1
            for d in self.data_list:
                view_item = self.convert_data_to_item(d, index)
                if view_item is None:
                    continue
                if not view_item.item_id in self.view_items_by_id:
                    self.view_items.append(view_item)
                    self.view_items_by_id[view_item.item_id] = view_item
                else:
                    self.log.warning((f"Duplicate ids in {self.view_id} : {view_item.as_dictionary()} and "
                                   f"{self.view_items_by_id[view_item.item_id].as_dictionary()}"))
                index += 1
            self.data_list = None

        return updated


    def get_view_items(self):
        self.data_added = False
        return super().get_view_items()


    def activate_view(self):
        super().activate_view()
        self.set_footer_hint(self.display_message, None)
        self.client.switch_view(self.edcopilot_display, self.display_item)