import logging
import pathlib
import queue
import threading
from threading import Thread
from unittest import TestCase

from edcopilot.socketclient import SocketClient


class DummySocket:
    def __init__(self):
        self.connected = True


class ReplayClient(SocketClient):
    """A client that validates expected sent messages and responds with responses recorded earlier"""
    def __init__(self, message_handler, test, data_dir, global_lock, panel, *, pre_response_hook=None):
        super().__init__(DummySocket(), "ReplayClient", message_handler, None, None)
        self.test: TestCase = test
        self.pre_response_hook = pre_response_hook
        self.global_lock = global_lock
        self.panel = panel
        files = pathlib.Path(data_dir).iterdir()
        files = sorted(files)
        self.file_pairs = []
        self.files_index = 0
        self.client_id = "1"

        self.response_thread = Thread(target=self.response_thread, daemon=True, name="ResponseClientSender")
        self.response_wait = threading.Event()
        self.response_shutdown = threading.Event()
        self.response_queue = queue.Queue()
        self.response_thread.start()

        self.expected_send  = []
        self.responses = []
        self.expected_send_index = 0
        self.log = logging.getLogger(self.__class__.__name__)

        for i in range(0, int(len(files) / 2)):
            infile = f"{i + 1}_sent.txt"
            outfile = f"{i + 1}_received.txt"

            if files[i * 2].name == outfile and files[i * 2 + 1].name == infile:
                self.file_pairs.append([files[i * 2 + 1], files[i * 2]])
            else:
                raise KeyError(f"Missing test file {infile} or {outfile}")

        self.read_files()


    def read_files(self):
        if self.files_index >= len(self.file_pairs):
            self.test.fail("Client received unexpected send message")

        self.expected_send_index = 0
        with open(self.file_pairs[self.files_index][0], "r") as f:
            self.expected_send = self.responses = [line.rstrip() for line in f.readlines()]

        if len(self.expected_send) == 0:
            self.test.fail(f"No expected send messages in {self.file_pairs[self.files_index][0]}")

        with open(self.file_pairs[self.files_index][1], "r") as f:
            self.responses = [line.rstrip() for line in f.readlines()]

        self.files_index += 1


    def validate(self):
        """Checks that all expected message were sent"""
        if self.expected_send and self.expected_send_index == len(self.expected_send):
            self.test.assertEqual(len(self.file_pairs), self.files_index)
        else:
            self.test.assertTrue(self.expected_send == [], f"expected_send not empty: {self.expected_send}")
            self.test.assertTrue(self.responses == [], f"responses not empty: {self.responses}")


    def send(self, message, waiting=False):
        if not self.expected_send or self.expected_send_index == len(self.expected_send):
            self.test.fail(f"Client received a send after all expected messages were sent: {message}")

        self.test.assertEqual(self.expected_send[self.expected_send_index], message)
        self.expected_send_index += 1
        self.log.debug(f"Received expected send: {message}")

        if self.expected_send_index == len(self.expected_send):
            if self.pre_response_hook:
                self.pre_response_hook()

            self.log.debug("Queueing up responses to be sent from another thread")
            if not waiting:
                # Regular responses with data need to be delayed so that they don't apply immediately
                # With a regular connection, the screen would be updated with a footer status message and an empty screen
                # If the responses are processed here, the initial update already has the data and no footer hint
                self.response_wait.clear()
                self.response_queue.put(self.responses)
            else:
                # If the caller is switch_view_and_wait, the thread may already be holding the global lock
                # Attempting to push the response send into the background thread will cause a 10-second delay as the wait times out
                # The response data is just an ack, so it can be safely processed immediately
                self.send_responses(self.responses)


    def switch_view_and_wait(self, view, item=None, option=None, ack_type=None):
        return super().switch_view_and_wait(view, item, option, ack_type)


    def close(self):
        super().close()
        self.response_shutdown.set()
        self.response_queue.shutdown(immediate=True)
        self.response_wait.set()


    def response_thread(self):
        while not self.response_shutdown.is_set():
            try:
                response_list = self.response_queue.get(block=True, timeout=1)
                self.log.debug(f"Received responses to send: {response_list}")
                if not self.response_wait.wait(60):
                    self.test.fail("Timed out waiting to send responses")

                with self.global_lock:
                    self.log.debug("Lock acquired")
                    updated = self.send_responses(response_list)

                    if updated:
                        self.panel.update_panel_json()
                    self.response_wait.clear()
                self.log.debug("Lock released")


            except queue.Empty:
                pass
            except queue.ShutDown:
                self.response_shutdown = True
                break
        self.log.debug("Response thread exiting")

    def send_responses(self, response_list) -> bool:
        updated = False
        for response in response_list:
            self.log.debug(f"Sending fake response message: {response}")
            updated |= self.process_connection_specific_message(response)
        if self.files_index < len(self.file_pairs):
            self.read_files()
        else:
            self.expected_send = []
            self.responses = []
        return updated
