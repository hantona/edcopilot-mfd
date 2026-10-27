import logging
import time


class SystemNameListener:
    """A class to listen for system name changes"""
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.system_name = ""

    def broadcast_handler(self, message):
        system_line_prefix = "<GUIINFO>System="
        if message.startswith(system_line_prefix):
            self.system_name = message.replace(system_line_prefix,"")
            self.log.debug(f"System name changed: {self.system_name}")


    def get_system_name(self):
        if not self.system_name:
            self.log.debug("System name is not set yet, waiting for a response")
            while not self.system_name:
                time.sleep(1)

        return self.system_name

