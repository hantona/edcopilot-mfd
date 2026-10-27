import unittest

from spansh_systems import SpanshSystems
from testing.testdata import test_file_path


class SpanshSystemsTest(unittest.TestCase):
    def test_get_station_factions(self):
        delkar_factions = {'Movement for Delkar Revolutionary Party', 'Delkar Company', 'Freedom Party of Delkar',
                           'Delkar Ltd', 'Delkar Jet Syndicate', 'Federal Reclamation Co'}
        spansh_systems = SpanshSystems(stations_file=test_file_path("EDCoPilot.SpanshSystems.txt"))
        factions = spansh_systems.get_station_factions("Delkar")
        self.assertEqual(delkar_factions, set(factions))


if __name__ == '__main__':
    unittest.main()
