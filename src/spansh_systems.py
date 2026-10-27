import logging
import re
from pathlib import Path

import psutil

class SpanshSystems:
    """Load the factions for each system from EDCoPilot's Spansh system cache"""
    def __init__(self, stations_file=None):
        self.stations_file = stations_file
        self.station_factions = {}
        self.log = logging.getLogger(self.__class__.__name__)


    @staticmethod
    def find_stations_file():
        result = None
        for process in psutil.process_iter():
            name = process.name()
            if name == "EDCoPilot" or name == "EDCoPilot.exe":
                result = Path(process.exe()).parent / "json files/EDCoPilot.SpanshSystems.txt"

                if not result.exists():
                    result = None

        return result


    def load_station_factions(self):
        if not self.stations_file:
            self.stations_file = self.find_stations_file()

        if self.stations_file:
            with open(self.stations_file, "r") as file:
                for line in file.readlines():
                    match = re.match("^([^=]*)=(.*)$", line)
                    if match:
                        system = match.group(1)
                        data = match.group(2)

                        fields = data.split("|")
                        if len(fields) <= 9:
                            self.log.error(f"Stations file data in an unexpected format: {line}")
                            return
                        factions = fields[8]
                        factions_list = factions.split("~")
                        self.station_factions[system] = factions_list

            if not "Delkar" in self.station_factions or not "Delkar Company" in self.station_factions["Delkar"]:
                self.log.warning("No factions found for Delkar, file format may have changed")


    def get_station_factions(self, system):
        if not self.station_factions:
            self.log.info("Loading all system factions")
            self.load_station_factions()
            self.log.info("System factions loading complete")

        return self.station_factions.get(system)
