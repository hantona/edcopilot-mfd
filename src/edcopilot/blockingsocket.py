import logging
import selectors
import socket

class BlockingSocket:
    """A soft-blocking socket wrapper for Windows

    The Windows socket recv call is hard blocking, which prevents signals from being delivered.
    This wrapper allows an interrupt signal to be processed to trigger a clean shutdown without a 10-second delay.
    """
    def __init__(self, family, proto):
        self.log = logging.getLogger(self.__class__.__name__)
        self.socket = socket.socket(family, proto)
        self.sel = selectors.DefaultSelector()
        self.connected = False
        self.selector_registered = False


    def setsockopt(self, level: int, optname: int, value: int, /):
        self.socket.setsockopt(level, optname, value)


    def connect(self, host_port):
        self.socket.connect(host_port)
        self.sel.register(self.socket, selectors.EVENT_READ)
        self.selector_registered = True


    def send(self, data):
        self.sendall(data)
        return len(data)


    def sendall(self, data):
        self.socket.sendall(data)


    def recv(self, size):
        recv_data = b''

        while not recv_data:
            # Blocks only until a socket is ready for I/O
            events = self.sel.select(timeout=1)
            for key, mask in events:
                # Key has application data, it's a client socket
                sock = key.fileobj

                if mask & selectors.EVENT_READ:
                    try:
                        recv_data = self.socket.recv(size)
                        if not recv_data:
                            # No data means the client closed the connection
                            self.log.error(f"Socket recv returned no data - closing connection")
                            self.sel.unregister(sock)
                            self.socket.close()
                            return recv_data
                    except ConnectionResetError:
                        self.log.error(f"Client abruptly disconnected.")
                        self.sel.unregister(sock)
                        self.socket.close()
                        return recv_data
                    except Exception as e:
                        self.log.exception("Unexpected error when calling socket receive", e)

                if mask & selectors.EVENT_WRITE:
                    self.log.warning("Write available event found when reading")

        return recv_data


    def close(self):
        if self.selector_registered:
            self.sel.unregister(self.socket)
        self.socket.close()
        self.sel.close()