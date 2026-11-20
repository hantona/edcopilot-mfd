import getpass
import json
import logging
import threading
import time

from pathlib import Path

from watchdog.events import PatternMatchingEventHandler, FileSystemEvent
from watchdog.observers import Observer

from data.armorprices import ship_remapping, armor_prices
from openreadonly import open_shared_read


class JournalWatcher(PatternMatchingEventHandler):
    """Watch the Elite Dangerous Journal files and proccess new events

    Saves the currently active ship type and the list of factions that have recently issued an unpaid bounty.
    """
    WINDOWS_JOURNAL_PATH = Path.home() / "Saved Games/Frontier Developments/Elite Dangerous"
    WSL_JOURNAL_PATH = Path(f"/mnt/c/Users/{getpass.getuser()}/Saved Games/Frontier Developments/Elite Dangerous")
    LINUX_JOURNAL_PATH = Path.home() / ".steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous"

    def __init__(self, *, journal_path=None):
        super().__init__(patterns=["*.log"])
        self.ship_remapping_lowercase = {}

        # An event to allow the test to wait for file events to be processed
        self.files_processed = threading.Event()

        self.ship_name = None
        self.wanted_factions = set()

        # Initial scan reads 3 days of journal files
        self.scan_start_time = time.time() - 3 * 24 * 60 * 60

        self.observer = Observer()
        self.log = logging.getLogger(self.__class__.__name__)

        for ship_id in ship_remapping.keys():
            self.ship_remapping_lowercase[ship_id.lower()] = ship_remapping[ship_id]

        for ship_name in armor_prices[list(armor_prices.keys())[0]]:
            self.ship_remapping_lowercase[ship_name.lower()] = ship_name

        if journal_path:
            self.journal_path = journal_path
        else:
            self.journal_path = self.find_journal()


    def start(self):
        self.observer.name = "JournalWatcher"
        self.observer.schedule(self, str(self.journal_path), recursive=True)
        self.observer.start()


    def stop(self):
        self.observer.stop()
        self.observer.join()


    def find_journal(self):
        if self.WINDOWS_JOURNAL_PATH.exists():
            return self.WINDOWS_JOURNAL_PATH
        elif self.WSL_JOURNAL_PATH.exists():
            return self.WSL_JOURNAL_PATH
        elif self.LINUX_JOURNAL_PATH.exists():
            return self.LINUX_JOURNAL_PATH
        else:
            raise FileNotFoundError("No journal directory found")


    def read_journals(self):
        files = sorted(self.journal_path.iterdir(), key=lambda journal_file: self.change_time(journal_file.stat()))
        recent_files = []
        newest_mtime = 0

        # self.log.debug("Start reading journals")
        for file in files:
            if not file.name.endswith(".log"):
                continue

            mtime = self.change_time(file.stat())
            if mtime > self.scan_start_time:
                recent_files.append(file)

            if mtime > newest_mtime:
                newest_mtime = mtime

        for file in recent_files:
            with (open_shared_read(file) as f):
                self.read_journal(f)

        self.scan_start_time = newest_mtime


    @staticmethod
    def change_time(stat):
        # When a file is renamed on Windows, the ctime is updated but not the mtime
        if stat.st_mtime > stat.st_ctime:
            return stat.st_mtime
        else:
            return stat.st_ctime


    def read_journal(self, file):
        self.log.debug(f"Reading journal file {file}")
        while line := file.readline():
            if "LoadGame" in line or "ShipyardSwap" in line or "ShipyardBuy" in line:
                self.handle_ship_event(line)
            elif "CommitCrime" in line or "PayBounties" in line or "ClearImpound" in line:
                self.handle_crime_event(line)

    def handle_ship_event(self, line):
        # The journal file does not consistently provide localized ship type names.
        # If the localized name is substantially different from the code name, it is included.
        # If the localized name would only differ by capitalization, it is not included.
        # An anaconda has ship code name 'anaconda', but the localized name of 'Anaconda' is not provided.
        # The capitalization is not consistent - the Sidewinder has code name 'SideWinder'.

        new_ship_localised = None
        entry = json.loads(line)

        if entry["event"] == "LoadGame":
            if "Ship_Localised" in entry:
                new_ship_localised = entry["Ship_Localised"]
            if "Ship" in entry:
                new_ship = entry["Ship"].lower()
                if not new_ship_localised and new_ship in self.ship_remapping_lowercase:
                    new_ship_localised = self.ship_remapping_lowercase[new_ship]
                elif not new_ship_localised:
                    self.log.error(f"Ship not in mapping: {new_ship}")

            if new_ship_localised is None:
                self.log.warning(f"No ship found in LoadGame journal: {line}")

        elif entry["event"] == "ShipyardSwap" or entry["event"] == "ShipyardBuy":
            if "ShipType_Localised" in entry:
                new_ship_localised = entry["ShipType_Localised"]
            if "ShipType" in entry:
                new_ship = entry["ShipType"].lower()
                if not new_ship_localised and new_ship in self.ship_remapping_lowercase:
                    new_ship_localised = self.ship_remapping_lowercase[new_ship]
                elif not new_ship_localised:
                    self.log.debug(f"Ship not in mapping: {new_ship}")

                if new_ship_localised is None:
                    self.log.warning(f"No ship found in shipyard journal: {line}")

        if self.ship_name != new_ship_localised:
            self.log.info(f"Ship changed from {self.ship_name} to {new_ship_localised}")
            self.ship_name = new_ship_localised


    def handle_crime_event(self, line):
        entry = json.loads(line)
        if entry["event"] == "ClearImpound":
            self.log.debug("Cleared impound - resetting wanted factions")
            self.wanted_factions.clear()
        elif entry["event"] == "PayBounties":
            faction = entry.get('Faction')
            all_fines = entry.get("AllFines")

            if faction:
                if faction in self.wanted_factions:
                    self.log.debug(f"Paid bounty for crime against {faction}")
                    self.wanted_factions.remove(faction)
                else:
                    self.log.warning(f"Paid a bounty for a crime against {faction} when it was not in the wanted set")
            elif all_fines:
                self.log.debug("Paid all bounties")
                self.wanted_factions.clear()
            else:
                self.log.warning("PayBounties journal entry did not contain Faction or AllFines")
        elif entry["event"] == "CommitCrime":
            faction = entry['Faction']
            self.log.debug(f"Committed a crime against faction {faction}")
            self.wanted_factions.add(faction)


    def get_ship_type(self):
        return self.ship_name


    def get_wanted_factions(self):
        return list(self.wanted_factions)


    def on_any_event(self, event: FileSystemEvent) -> None:
        # self.log.debug(f"Received journal file change event: {event}")
        self.read_journals()
        self.files_processed.set()
