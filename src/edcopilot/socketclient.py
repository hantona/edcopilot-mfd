import logging
import re
import threading
import time


class SocketClient:
    """A virtual EDCoPilot connection that represents a unique UI with server side state"""
    client_id_ms_offset = 0

    # Some of the ack messages don't match the original command name
    ack_to_view = {"commoditysearchtype": "SetCommodity"}

    def __init__(self, edcopilot_socket, client_name, message_handler, ready_handler, broadcast_handler):
        self.edcopilot_socket = edcopilot_socket
        self.client_name = client_name
        self.ready_handler = ready_handler
        self.message_handler = message_handler
        self.broadcast_handler = broadcast_handler
        self.client_id = None
        self.connectionIdMs = 0
        self.wait_conditions = {}
        self.acks_received = {}
        self.ack_callbacks = {}
        self.connection_id_ms = None
        self.connection_request_sent = False
        self.client_id_set_event = threading.Event()

        self.log = logging.getLogger(self.__class__.__name__)


    def ready(self):
        if self.ready_handler is not None:
            self.ready_handler()

    def close(self):
        pass

    def get_client_id(self):
        if self.client_id is None:
            raise ValueError(f"get_client_id called on client {self.client_name} before client id was set")
        return self.client_id


    def reset_client(self):
        self.client_id = None
        self.connection_id_ms = None
        self.acks_received = {}
        for message in self.wait_conditions.keys():
            with self.wait_conditions[message]:
                self.wait_conditions[message].notify_all()

        self.wait_conditions = {}
        self.connection_request_sent = False


    def id_set(self):
        return self.client_id is not None


    def send_client_id_request(self):
        if not self.connection_request_sent:
            # Add in an incrementing number to avoid generating the same id twice in the same millisecond
            self.connection_id_ms = str(time.time_ns() // 1_000_000 + self.client_id_ms_offset)
            self.client_id_ms_offset = SocketClient.client_id_ms_offset + 1
            self.log.debug(f"Requesting EDCoPilot client id for {self.client_name}")
            self.edcopilot_socket.send(f"#NEW-{self.connection_id_ms}:CONNECT:WorthIT-UI:127.0.0.1")
            self.connection_request_sent = True
        else:
            self.log.error("send_client_id_reequest called more than once for a client")

    def process_client_id_response(self, line):
        processed = False

        new_client_id_match = re.search("^#NEW-([0-9.]+):<GUISETID>", line)
        if new_client_id_match:
            connection_id_ms = new_client_id_match.group(1)
            if connection_id_ms == self.connection_id_ms:
                # The new client response contains the client id that is used as a prefix on all the messages for the client
                connection_id = re.sub(".*:<GUISETID>", "", line)
                self.set_client_id(connection_id)
                self.log.debug(f"Set EDCoPilot client id for {self.client_name} to {connection_id}")
                processed = True
        else:
            self.log.error(f"Received unexpected client id from websocket: {line}")

        return processed


    def send(self, message, waiting=False):
        self.get_client_id()

        self.log.debug(f"Sending message for client {self.client_name}: {message}")
        self.edcopilot_socket.send(message)


    def switch_view(self, view, item=None, option=None, callback=None, waiting=False):
        specifier = view

        if callback:
            self.acks_received[view] = False
            self.ack_callbacks[view] = callback

        if item:
            specifier += ':' + item

        if option:
            specifier += ':' + option

        self.send(f"<switchTo:#{self.get_client_id()}:{specifier}:endSwitch>", waiting=waiting)


    def switch_view_and_wait(self, view, item=None, option=None, ack_type=None):
        if ack_type is None:
            ack_type = view

        if view in self.wait_conditions:
            condition = self.wait_conditions[ack_type]
        else:
            condition = threading.Condition()
            self.wait_conditions[ack_type] = condition

        self.acks_received[view] = False
        self.switch_view(view, item, option, waiting=True)

        self.log.debug(f"Switched to view {view} and waiting for response")
        with condition:
            condition.wait_for(lambda: ack_type not in self.acks_received or self.acks_received[ack_type], 10)
        ack_received = self.acks_received[ack_type]

        if ack_received:
            self.log.debug(f"Received response for view switch to {view}")
        else:
            self.log.debug(f"Failed to receive a response for view switch to {view}")
        self.acks_received[ack_type] = False
        return ack_received

    def set_client_id(self, client_id):
        self.client_id = client_id
        self.client_id_set_event.set()

    def process_ack(self, switched_to: str, original_command):
        self.log.debug(f"Received {switched_to} ack for client {self.client_name}")
        if original_command in self.wait_conditions:
            # Waking up the original sending thread
            self.acks_received[original_command] = True
            with self.wait_conditions[original_command]:
                self.wait_conditions[original_command].notify_all()

        if original_command in self.ack_callbacks:
            if self.ack_callbacks[original_command] is not None:
                self.log.debug(f"Invoking ack callback for {original_command}")
                self.ack_callbacks[original_command]()
                self.ack_callbacks[original_command] = None
            else:
                self.log.warning(f"No response callback for {original_command} - possible duplicate response")


    def process_connection_specific_message(self, content) -> bool:
        data_processed = False

        if self.message_handler is None:
            raise ValueError("Message handler not set")

        match = re.search("^<([a-zA-Z]+)>(.*)", content)
        if match:
            message_type = match.group(1)
            message_content = match.group(2)
            if not (message_type == "GCClear" or (
                    message_type == "GCDetail" and message_content == "-|-|-|-|-|-1||||")):
                self.message_handler(message_type, message_content)
                data_processed = True
        else:
            match = re.search("^<switchTo:([a-zA-Z]+):endSwitch>$", content)
            if match:
                switched_to = match.group(1)
                # When a sequence of commands is sent, each one often is not valid until the server acknowledges the previous one.
                # Even when sending immediately appears to work, it can subtly break.
                # For example, sending a human or guardian tech broker search before receiving the 'locationsearch' response
                # results in the search results being sent to a randomly selected EDCopilot client.
                original_command = self.ack_to_view.get(switched_to) or switched_to
                self.log.debug(f"Received {switched_to} ack for message type {original_command}")
                self.process_ack(switched_to, original_command)
            elif re.match("^[0-9]{2}:[0-9]{2}:[0-9]{2} ", content):
                # Voice Log
                pass
            else:
                self.log.error(f"Unexpected message format: {content}")
        return data_processed