import typing

from items.locationlistitem import LocationListItem
from spansh_systems import SpanshSystems
from views.locationview import LocationView


class InterstellarFactorsView(LocationView):
    """A list of the closest Interstellar Factors locations

    An extra Wanted attribute is added if the commander has a recent bounty from any faction in the system
    """
    def __init__(self, spansh_systems: SpanshSystems, journal_watcher) -> None:
        super().__init__("Interstellar Factors","GetInterstellar",
                         display_message="Waiting for the nearby Interstellar Factors")
        self.spansh_systems = spansh_systems
        self.journal_watcher = journal_watcher


    def convert_data_to_item(self, data, index):
        item = typing.cast(LocationListItem,  super().convert_data_to_item(data, index))

        wanted = self.journal_watcher.get_wanted_factions()
        system_factions = self.spansh_systems.get_station_factions(item.system)
        wanted_in_system = set(wanted) & set(system_factions)
        wanted_y_n = 'Y' if wanted_in_system else 'N'

        item.sublabel += ", Wanted=" + wanted_y_n

        return item
