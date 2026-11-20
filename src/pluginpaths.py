import logging
import os
import sys
from pathlib import Path

# Lookup utilities for finding the MFD interface files

PROGRAM_FILES = os.environ.get("ProgramFiles", "")
PROGRAM_FILES_X86 = os.environ.get("ProgramFiles(x86)", "")

WINDOWS_BASE_STEAM = PROGRAM_FILES_X86 + "/Steam/steamapps/common/Elite Dangerous/Products"
WSL_BASE_STEAM = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Elite Dangerous/Products"
LINUX_BASE_STEAM = os.path.expanduser("~/.steam/steam/SteamApps/common/Elite Dangerous/Products")

WINDOWS_BASE_EPIC = PROGRAM_FILES + "/Epic Games/EliteDangerous/Products"
WINDOWS_BASE_FRONTIER = PROGRAM_FILES_X86 + "/Frontier/Products"

HORIZONS_PRODUCT = "elite-dangerous-64"
ODYSSEY_PRODUCT = "elite-dangerous-odyssey-64"

# edvr-mfd may rename to edup_mfd
EDVR_MFD = "edvr_mfd"

MFD_PLUGIN_PATH = f"plugins/{EDVR_MFD}/mfds/edcopilot"

SCREEN_PATH = "screens/edcopilot.json"
EVENTS_PATH = "events.jsonl"
LOCK_PATH = "companion.lock"

def get_screen_path():
    """Get the path to the MFD screen JSON file"""
    return build_plugin_path(SCREEN_PATH)


def get_events_path():
    """Get the path to the MFD event file"""
    return build_plugin_path(EVENTS_PATH)


def get_lock_path():
    """Get the path to the lock file used to prevent an IDE from starting multiple instances"""
    return build_plugin_path(LOCK_PATH)


# Check if the working directory is the one for this MFD so that Steam path guessing can be skipped
def running_from_ed():
    return Path.cwd().parent.name == "mfds" and Path.cwd().parent.parent.name == EDVR_MFD


def build_plugin_path(relative):
    # If EDVR is running the script, the working directory will be the mfds/edcopilot
    # If that isn't the working directory, try to guess the game path
    if running_from_ed():
        # Use the fully qualified path to avoid passing the empty string as a directory to the event file watcher
        return str(Path(relative).absolute())
    else:
        for potential_base in [WINDOWS_BASE_STEAM, WINDOWS_BASE_EPIC, WINDOWS_BASE_FRONTIER, WSL_BASE_STEAM,
                               LINUX_BASE_STEAM]:
            if os.path.exists(potential_base):
                mfd_path = find_directory_in_base(potential_base)
                if mfd_path:
                    return f"{mfd_path}/{relative}"

        logging.error("No MFD plugin path detected")
        sys.exit(1)


def find_directory_in_base(product_base):
    """Adds the product directory to the base path depending on if the user has Odyssey"""
    game_base = None

    if product_base:
        if os.path.exists(f"{product_base}/{ODYSSEY_PRODUCT}"):
            game_base = f"{product_base}/{ODYSSEY_PRODUCT}"
        elif os.path.exists(f"{product_base}/{HORIZONS_PRODUCT}"):
            game_base = f"{product_base}/{HORIZONS_PRODUCT}"

        if game_base is not None:
            mfd_plugin = f"{game_base}/{MFD_PLUGIN_PATH}"
            if os.path.exists(mfd_plugin):
                return mfd_plugin

    return None

