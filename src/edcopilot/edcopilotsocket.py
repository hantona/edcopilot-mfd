import json
import socket
import time
import re
from threading import Thread

import logging

from edcopilot import blockingsocket
from edcopilot.socketclient import SocketClient
from testing.messagelogger import MessageLogger

EDCOPILOT_PORT = 9096

class EDCopilotSocket:
    """A connection to the EDCopilot service

    The connection supports multiple virtual connections over the same physical connection.
    Responses are tagged with the id of the virtual connection or with '*' if the message is for all connections."""

    def __init__(self, status, global_lock, open_handler=None, hostname="127.0.0.1"):
        self.log = logging.getLogger(self.__class__.__name__)

        self.status = status
        self.global_lock = global_lock
        self.hostname = hostname

        self.broadcast_handlers = []
        self.completion_handlers = []
        self.disconnect_handlers = []
        self.other_client_handlers = []

        self.clients: list[SocketClient] = []
        self.open_handler = open_handler

        self.partial_message = ""

        self.socket = None
        self.connected = False
        self.ready = False
        self.exit = False
        self.voicelog_seen = False

        self.ping_thread = None

        self.add_broadcast_handler(self.startup_progress_handler)


    def find_client_by_id(self, client_id):
        for client in self.clients:
            if client.client_id == client_id:
                return client

        return None


    def create_client(self, client_name, message_handler=None, ready_handler=None,
                      broadcast_handler=None, message_log_dir=None):

        if message_log_dir is None:
            client = SocketClient(self, client_name, message_handler, ready_handler, broadcast_handler)
        else:
            client = MessageLogger(self, client_name, message_handler, ready_handler, broadcast_handler,
                                   message_log_dir)
        self.clients.append(client)

        # If the client isn't connected yet, queue the client object up for initialization later
        if self.connected:
            client.send_client_id_request()

        return client


    def on_message(self, message):
        data_processed = False

        try:
            if not message.endswith("\n\n"):
                self.partial_message += message
                return
            elif self.partial_message != "":
                message = self.partial_message + message
                self.partial_message = ""

            with self.global_lock:
                for line in message.split("\n\n"):
                    if line.startswith("#NEW-"):
                        self.handle_connect_response(line)
                    elif line.startswith("#*:"):
                        content = re.sub("^#\\*+:", "", line)
                        for broadcast_handler in self.broadcast_handlers:
                            broadcast_handler(content)

                        for client in self.clients:
                            self.process_connection_specific_message(f"#{client.client_id}:{content}")
                        data_processed = True
                    elif line.startswith("#"):
                        data_processed |= self.process_connection_specific_message(line)
                    elif line.startswith("{"):
                        self.send_ping_response(line)
                    else:
                        continue

                if data_processed:
                    self.completion_handler()
        except Exception as e:
            self.log.exception("Failure processing EDCopilot message", e)


    def handle_connect_response(self, line):
        response_client = None

        for client in self.clients:
            if client.process_client_id_response(line):
                response_client = client

        if not response_client:
            self.log.debug(f"Received connection message for another client {line}")
        else:
            if self.ping_thread is None:
                # Pings must only be sent after the connection id is established
                self.ping_thread = PingThread(self)
                self.ping_thread.start()

            self.reconnect_first_client()


    def process_connection_specific_message(self, line) -> bool:
        data_processed = False
        if client_id_match := re.search("^#(\\d+):(.*)", line):
            client_id = client_id_match.group(1)
            content = client_id_match.group(2)

            client = self.find_client_by_id(client_id)
            if client is None:
                # Send the messages for unknown clients to a message handler
                # EDCopilot sometimes misdirect responses to the wrong client
                # This is most common with the tech broker search responses
                for other_client_handler in self.other_client_handlers:
                    other_client_handler(client_id, content)
                pass
            else:
                if content == "<GUIUNLOCK>":
                    self.log.info("Connection is ready to accept commands")
                    client.ready()
                    self.status.mark_connected()
                elif content == "<switchTo:voicelog:endSwitch>":
                    self.log.info("Voice log message seen - sleeping before sending more messages")
                    # Sleep before sending the GetExternalDataFirst message for the first time after connecting
                    # If EDCopilot was just restarted, sending the message immediately will crash it
                    if not self.voicelog_seen:
                        time.sleep(20)
                        self.voicelog_seen = True

                    client.switch_view("GetExternalDataFirst")
                    self.completion_handler()
                else:
                    data_processed = client.process_connection_specific_message(content)
        else:
            self.log.debug(f"Message did not contain a client id and content: {line}")
        return data_processed


    def send_ping_response(self, line):
        json_message = json.loads(line)
        if json_message["msgType"] == "GUIPING" and json_message["guiID"] == "*":
            ping_iteration = json_message["iter"]
            for client in self.clients:
                ip_address = self.hostname
                self.send(
                    f"GUIPINGREPLY:{client.client_id}:{ip_address}:{ping_iteration}")


    def on_open(self):
        self.log.debug("Opened EDCoPilot connection")
        self.reconnect_first_client()

        if self.open_handler:
            self.open_handler()


    def reconnect_first_client(self):
        self.log.debug("Reconnecting first EDCoPilot client without an id")
        for client in self.clients:
            if not client.id_set():
                client.send_client_id_request()
                break


    def start(self):
        self.connect()

        while not self.exit:
            message = self.receive()
            if message is not None:
                self.on_message(message)


    def stop(self):
        self.exit = True
        self.close()


    def connect(self):
        # supress sequential logging of connection failures
        last_log_message = ""

        self.log.debug(f"Connecting to {self.hostname}:{EDCOPILOT_PORT}")
        self.voicelog_seen = False
        while not self.connected and not self.exit:
            try:
                self.socket = blockingsocket.BlockingSocket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.socket.connect((self.hostname, EDCOPILOT_PORT))
                self.log.debug("Connected to EDCoPilot service")
                self.connected = True
                self.on_open()
            except ConnectionRefusedError:
                log_message = "EDCopilot connection refused"
                if log_message != last_log_message:
                    self.log.error(log_message)
                    last_log_message = log_message

                self.socket.close()
                self.socket = None
                time.sleep(2)
            except SystemExit:
                if self.socket is not None:
                    self.socket.close()
                    self.socket = None
            except (OSError | TimeoutError) as e:
                log_message = "EDCopilot socket connection failed"
                if log_message != last_log_message:
                    self.log.exception(log_message, e)
                    last_log_message = log_message
                self.socket.close()
                self.socket = None


    def send(self, message, newline=True):
        try:
            if newline:
                message = message + "\n"
            if 'GUIPING' not in message:
                self.log.debug(f"Sent message to EDCoPilot: {message.rstrip()}")
            sent = 0
            if self.socket is not None and self.connected:
                sent = self.socket.sendall(message.encode("utf-8"))
            else:
                self.log.error("Send called on a closed socket")
            if sent == 0:
                raise RuntimeError("socket connection broken")
        except ConnectionResetError:
            self.log.error("Connection reset while sending data")
            self.close()
        except ConnectionAbortedError:
            self.log.error("Connection aborted while sending data")
            self.close()
        except Exception as e:
            self.log.exception("EDCopilot socket send error", e)


    def receive(self):
        result: str | None = None
        try:
            if self.connected:
                chunk = self.socket.recv(64 * 1024)
                if chunk == b'':
                    self.log.error("Disconnected while reading from the socket")
                    self.already_closed()
                else:
                    result = chunk.decode("utf-8")

            if not self.connected:
                self.connect()
        except (ConnectionResetError, ConnectionAbortedError) as e:
            self.log.exception("Connection reset while receiving from the socket", e)
            self.close()
            self.connect()

        return result


    def close(self):
        if self.socket is not None:
            for client in self.clients:
                client.close()

            self.log.debug("Closing EDCoPilot connection")
            self.socket.close()
            self.already_closed()


    def already_closed(self):
        self.connected = False
        self.ready = False
        self.socket = None
        self.voicelog_seen = False

        self.status.mark_disconnected()
        self.disconnect_handler()
        if self.ping_thread:
            self.ping_thread.stop()
            self.ping_thread = None

        for client in self.clients:
            client.reset_client()


    def add_broadcast_handler(self, handler):
        self.broadcast_handlers.append(handler)


    def add_completion_handler(self, handler):
        self.completion_handlers.append(handler)


    def add_disconnect_handler(self, handler):
        self.disconnect_handlers.append(handler)


    def add_other_client_handler(self, handler):
        self.other_client_handlers.append(handler)


    def completion_handler(self):
        for completion_handler in self.completion_handlers:
            completion_handler()


    def disconnect_handler(self):
        for disconnect_handler in self.disconnect_handlers:
            disconnect_handler()


    def startup_progress_handler(self, content):
        # When EDCopilot needs to download updated station information on startup, the
        # progress updates are sent in DUProgress messages.
        if content.startswith("<DUProgress>"):
            message = content.replace("<DUProgress>", "")
            self.log.debug(f"Setting connection status message to {message}")
            self.status.set_disconnected_message(message)


class PingThread(Thread):
    def __init__(self, edcopilot_socket):
        self.log = logging.getLogger(self.__class__.__name__)
        super().__init__(daemon=True, name="Ping")
        self.edcopilot_socket = edcopilot_socket
        self.continue_running = True

    def run(self):
        self.log.info("Socket ping started")
        while self.continue_running:
            for i in range(30):
                time.sleep(1)
                if not self.continue_running:
                    return

            if self.edcopilot_socket.connected:
                self.edcopilot_socket.send("<GUIPING>", newline=False)

    def stop(self):
        self.continue_running = False