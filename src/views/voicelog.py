import re

from baseview.view import View
from items.textitem import TextItem

# Limit the number of voice log lines displayed
MAX_LOG_LINES = 100


class VoicelogView(View):
    """Displays the recent messages spoken by EDCoPilot"""
    def __init__(self):
        super().__init__("Voice Log", view_type="text")

        self.updated = True
        self.last_added = ""


    def build_items(self):
        updated_now = self.updated
        self.updated = False
        return updated_now


    def activate_view(self):
        # Skip super to avoid getting a client
        # Voice log is the default view, so the command to switch to it is not required
        self.updated = True


    def append_log_line(self, log_line):
        if re.search("^\\d\\d:\\d\\d:\\d\\d ", log_line):
            # There is an EDCopilot bug that is causing every log line to be sent twice
            if log_line != self.last_added:
                self.view_items.insert(0, TextItem(self.view_id, log_line))
                self.updated = True
                self.last_added = log_line

                if len(self.view_items) > MAX_LOG_LINES:
                    self.view_items = self.view_items[:MAX_LOG_LINES]


    def get_view_item(self, item_id):
        return super().get_view_item(item_id)


    @staticmethod
    def needs_client():
        return False