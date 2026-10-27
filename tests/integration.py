import logging
import time
import unittest
from threading import Thread

from main import Application
from mfdclient.client import Client


class DataListener(Client):
    def __init__(self, test):
        super().__init__(self.data_loaded, self.data_changed)
        self.test = test
        self.updated = True
        self.timeout = 20
        self.current_tab = None

    def data_loaded(self):
        pass

    def wait_for_item(self, item_id=None, item_label=None):
        logging.debug(f'Waiting for item {item_id} {item_label} in {self.current_tab}...')
        timeout = self.timeout
        self.updated = True

        while timeout > 0:
            if self.updated:
                item = self.find_item(item_id=item_id, item_label=item_label)

                if item is not None:
                    return item

            time.sleep(1)
            timeout -= 1

        self.test.fail(f'Timed out while waiting for item {item_id} {item_label} in {self.current_tab}...')
        return None

    def data_changed(self):
        self.updated = True

class IntegrationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DataListener(self)

    @staticmethod
    def wait_for_ready(status):
        while not status.connected:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                logging.debug("Keyboard interrupt")
                break

    def test_price_lookups(self):
        application = Application(add_shutdown_hook=False, multi_instance_lock=False)

        Thread(target=application.run).start()
        self.wait_for_ready(application.status)
        logging.debug("test ready")

        self.simple_view_check("Places", "Interstellar Factors")
        self.simple_view_check("Places", "Raw Materials Trader")
        self.simple_view_check("Places", "Encoded Materials Trader")
        self.simple_view_check("Places", "Manufactured Materials Trader")
        self.simple_view_check("Places", "Repair")
        self.simple_view_check("Places", "Black Market")
        self.simple_view_check("Places", "Guardian Technology Broker")
        self.simple_view_check("Places", "Human Technology Broker")
        # CommoditiesView(edcopilot_socket),
        # OutfittingView(edcopilot_socket),
        # ShipPurchaseView(edcopilot_socket),
        application.stop()

    def simple_view_check(self, tab_id, item_id):
        self.client.switch_tab(tab_id)
        item = self.client.wait_for_item(item_id=item_id)
        logging.debug(str(item))

        self.client.select_item(item[0])
        logging.debug(f"Item was at index {item[0]}")
        location_item = self.client.wait_for_item(item_id="1")
        logging.debug(str(location_item))
        logging.debug(f"Found {item_id} location {location_item[1]}")
        logging.debug(str(item))

        self.client.back(0)
        item = self.client.wait_for_item(item_id=item_id)



if __name__ == '__main__':
    unittest.main()
