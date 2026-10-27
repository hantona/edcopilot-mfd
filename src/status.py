DEFAULT_DISCONNECTED_MESSAGE = "Waiting for connection to EDCopilot..."


class Status:
    """A class for sharing connection status between the EDCoPilot socket and the Panel"""
    def __init__(self):
        self.text = "Connecting"
        self.color = "ok"
        self.content_updated = True
        self.connected = False
        self.disconnected_message = DEFAULT_DISCONNECTED_MESSAGE


    def mark_disconnected(self):
        self.text = "Disconnected"
        self.color = "crit"
        self.content_updated = True
        self.connected = False
        self.disconnected_message = DEFAULT_DISCONNECTED_MESSAGE


    def mark_connected(self):
        self.text = "Connected"
        self.color = "ok"
        self.content_updated = True
        self.connected = True


    def updated(self):
        result = self.content_updated

        if self.content_updated:
            self.content_updated = False

        return result


    def is_connected(self):
        return self.connected


    def get_disconnected_message(self):
        return self.disconnected_message


    def set_disconnected_message(self, message):
        self.disconnected_message = message
