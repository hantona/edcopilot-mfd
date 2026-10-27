from edcopilot.socketclient import SocketClient

class MessageLogger(SocketClient):
    """A subclass of SocketClient that saves all messages sent and received"""
    def __init__(self, edcopilot_socket, client_name, message_handler, ready_handler, broadcast_handler,
                 output_dir):
        super().__init__(edcopilot_socket, client_name, message_handler, ready_handler, broadcast_handler)

        self.sent_messages = []
        self.received_messages = []

        self.output_dir = output_dir
        self.file_number = 1


    def close(self):
        super().close()
        if self.sent_messages or self.received_messages:
            self.write_messages()


    def write_messages(self):
        with open(f"{self.output_dir}/{self.file_number}_sent.txt", "w") as f:
            for message in self.sent_messages:
                f.write(f"{message}\n")

        with open(f"{self.output_dir}/{self.file_number}_received.txt", "w") as f:
            for message in self.received_messages:
                f.write(f"{message}\n")

        self.sent_messages = []
        self.received_messages = []
        self.file_number += 1


    def send(self, message, waiting=False):
        if self.received_messages:
            self.write_messages()

        self.sent_messages.append(message)
        super().send(message, waiting=waiting)


    def process_connection_specific_message(self, content) -> bool:
        self.received_messages.append(content)
        return super().process_connection_specific_message(content)

