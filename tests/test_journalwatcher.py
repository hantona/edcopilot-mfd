import logging
import shutil
import time
import unittest
from pathlib import Path

from journalwatcher import JournalWatcher
from testing import testdata


class JournalWatcherTest(unittest.TestCase):
    def test_single_record(self):
        watcher = JournalWatcher()

        with open(testdata.test_file_path("journal_watcher/load_game.json")) as f:
            watcher.read_journal(f)
        self.assertEqual("Cobra Mk III", watcher.get_ship_type())

        with open(testdata.test_file_path("journal_watcher/load_game_anaconda.json")) as f:
            watcher.read_journal(f)
        self.assertEqual("Anaconda", watcher.get_ship_type())


        with open(testdata.test_file_path("journal_watcher/shipyard_buy.json")) as f:
            watcher.read_journal(f)
        self.assertEqual("Cobra Mk III", watcher.get_ship_type())

        with open(testdata.test_file_path("journal_watcher/shipyard_buy_anaconda.json")) as f:
            watcher.read_journal(f)
        self.assertEqual("Anaconda", watcher.get_ship_type())

        with open(testdata.test_file_path("journal_watcher/shipyard_swap.json")) as f:
            watcher.read_journal(f)
        self.assertEqual("Cobra Mk III", watcher.get_ship_type())

        with open(testdata.test_file_path("journal_watcher/shipyard_swap_anaconda.json")) as f:
            watcher.read_journal(f)
        self.assertEqual("Anaconda", watcher.get_ship_type())

    @staticmethod
    def combine_files(output_file_name, *files):
        with open(output_file_name, mode="w") as output_file:
            for file in files:
                qualified_file_path = testdata.test_file_path(file)
                with open(qualified_file_path) as input_file:
                    lines = input_file.readlines()
                    for line in lines:
                        output_file.write(line + "\n")

    def test_multiple_records(self):
        watch_dir = testdata.temp_path()
        watch_dir.mkdir(parents=True, exist_ok=True)
        watcher = JournalWatcher(journal_path=str(watch_dir))

        combined = watch_dir / "journal-watcher-tailing.log"
        self.combine_files(combined, "journal_watcher/load_game.json", "journal_watcher/load_game_anaconda.json")
        with open(combined) as f:
            watcher.read_journal(f)
        self.assertEqual("Anaconda", watcher.get_ship_type())

        self.combine_files(combined, "journal_watcher/load_game_anaconda.json", "journal_watcher/load_game.json")
        with open(combined) as f:
            watcher.read_journal(f)
        self.assertEqual("Cobra Mk III", watcher.get_ship_type())


    def test_multiple_files(self):
        watch_dir = testdata.temp_path()
        if watch_dir.exists():
            shutil.rmtree(watch_dir)
        watch_dir.mkdir(parents=True, exist_ok=True)
        watcher = JournalWatcher(journal_path=watch_dir)

        self.copy_and_rename("journal_watcher/load_game.json", "load_game.json", watch_dir)
        self.copy_and_rename("journal_watcher/load_game_anaconda.json", "load_game_anaconda.json", watch_dir)
        watcher.read_journals()
        self.assertEqual("Anaconda", watcher.get_ship_type())


        # Switch the modification times to verify that the newer file overrides
        (watch_dir / "load_game.log").touch()
        watcher.read_journals()
        self.assertEqual("Cobra Mk III", watcher.get_ship_type())


    def test_file_tailing(self):
        logging.basicConfig(level=logging.DEBUG)
        watch_dir = testdata.temp_path()
        if watch_dir.exists():
            shutil.rmtree(watch_dir)
        watch_dir.mkdir(parents=True, exist_ok=True)
        watcher = JournalWatcher(journal_path=watch_dir)
        watcher.start()

        self.assertIsNone(watcher.get_ship_type())

        watcher.files_processed.clear()
        self.copy_and_rename("journal_watcher/load_game.json", "load_game.json", watch_dir)
        watcher.files_processed.wait(10)
        self.assertEqual("Cobra Mk III", watcher.get_ship_type())

        watcher.files_processed.clear()
        self.copy_and_rename("journal_watcher/load_game_anaconda.json", "load_game_anaconda.json", watch_dir)
        watcher.files_processed.wait(10)
        self.assertEqual("Anaconda", watcher.get_ship_type())

        watcher.files_processed.clear()
        watcher.stop()
        self.copy_and_rename("journal_watcher/load_game.json", "load_game2.json", watch_dir)
        time.sleep(3)
        self.assertEqual("Anaconda", watcher.get_ship_type())


    def test_bounty_pay_individual(self):
        watch_dir = testdata.temp_path()
        watch_dir.mkdir(parents=True, exist_ok=True)
        watcher = JournalWatcher(journal_path=str(watch_dir))

        self.read_journal(watcher, "journal_watcher/commit_crime1.json")
        self.assertEqual({"Intergalactic Nova Republic"}, watcher.wanted_factions)

        self.read_journal(watcher, "journal_watcher/commit_crime2.json")
        self.assertEqual({"Federal Reclamation Co", "Intergalactic Nova Republic"}, watcher.wanted_factions)

        self.read_journal(watcher, "journal_watcher/pay_bounty1.json")
        self.assertEqual({"Federal Reclamation Co"}, watcher.wanted_factions)

    def test_bounty_pay_all(self):
        watch_dir = testdata.temp_path()
        watch_dir.mkdir(parents=True, exist_ok=True)
        watcher = JournalWatcher(journal_path=str(watch_dir))

        self.read_journal(watcher, "journal_watcher/commit_crime1.json")
        self.assertEqual({"Intergalactic Nova Republic"}, watcher.wanted_factions)

        self.read_journal(watcher, "journal_watcher/commit_crime2.json")
        self.assertEqual({"Federal Reclamation Co", "Intergalactic Nova Republic"}, watcher.wanted_factions)

        self.read_journal(watcher, "journal_watcher/pay_bounty_all.json")
        self.assertEqual(set(), watcher.wanted_factions)

    def test_bounty_impounded(self):
        watch_dir = testdata.temp_path()
        watch_dir.mkdir(parents=True, exist_ok=True)
        watcher = JournalWatcher(journal_path=str(watch_dir))

        self.read_journal(watcher, "journal_watcher/commit_crime1.json")
        self.assertEqual({"Intergalactic Nova Republic"}, watcher.wanted_factions)

        self.read_journal(watcher, "journal_watcher/commit_crime2.json")
        self.assertEqual({"Federal Reclamation Co", "Intergalactic Nova Republic"}, watcher.wanted_factions)

        self.read_journal(watcher, "journal_watcher/clear_impound.json")
        self.assertEqual(set(), watcher.wanted_factions)


    @staticmethod
    def read_journal(watcher: JournalWatcher, journal_file="journal_watcher/commit_crime1.json"):
        with open(testdata.test_file_path(journal_file)) as f:
            watcher.read_journal(f)

    @staticmethod
    def copy_and_rename(src_file, dest_name, watch_dir: Path):
        src = Path(testdata.test_file_path(src_file))
        destination = watch_dir / dest_name
        shutil.copy2(src, destination)
        destination.rename(watch_dir / destination.name.replace(".json", ".log"))


if __name__ == '__main__':
    unittest.main()
