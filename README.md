# EDCopilot-MFD

EDCopilot-MFD displays parts of the EDCopilot interface in an EDVR MFD display.

The display requires EDCopilot and EDCopter to be running.

## Features
* Native keyboard and HOTAS navigation
* Optimized for compact display (distances rounded, redundant fields excluded)
* Large lists like commodities and outfitting parts split into categories
* Mining hotspot search filtered to only the commodities that have hotspots
* Displays live heading and distance to known biological samples
* Outfitting search includes prices for equipment and armor

## Known Issues

This UI works somewhat differently than the other EDCopilot UIs.  It 
sends the same commands as the other UIs currently do, but it is much
less flexible in handling changes to the core UI design.  It is possible 
that design changes in the main UI will break this one until the code is
updated to match. EDCopilot automatically updates itself, so this failure
could happen unexpectedly.  


The categories and prices are hard-coded because there is no good source
for that data and I don't want to live scrape Inara on every user's
machine.  Hopefully items and prices are not changed frequently enough
for this to be a problem.  Unexpected commodities or equipment will
display in an 'Other' category until the category list is updated to
include the new item.  New equipment will not have prices, but the
bundled price data is already more current than the EDCopilot search
results.  The EDCopilot outfitting search is already missing suits and
personal equipment and some newer ship items, such as items bought with
MC.  

The Inventory and Management tabs have not been added.  Only the Voice
Log from the Activity tab is included.  The full options menu for
stations has not been added, but could be if people would find it useful.
Without a second action button, the station options would add another
menu level and click for every station navigation.  

The display is probably broken if the game is not running in English.  I
haven't figured out how to run the game in another language to test what
changes in the EDCopilot data and the journal files.  

## Installation

Install EDVR MFD 0.1.0 or newer from https://github.com/dmnemec/edvr-mfd/releases.

To install this display, unzip the archive and copy the edcopilot
directory to elite-dangerous-odyssey-64/plugins/edvr_mfd/mfds/edcopilot
and restart Elite Dangerous.

On Windows, the mfds directory should be at C:\Program Files (x86)\Steam\steamapps\common\Elite Dangerous\Products\elite-dangerous-odyssey-64\plugins\edvr_mfd\mfds.
On Linux, the path should be 
~/.steam/steam/SteamApps/common/Elite Dangerous/Products/elite-dangerous-odyssey-64/plugins/edvr_mfd/mfds.

## Building

Building from source requires Python 3.11 or newer.

Running build.bat or build.sh will create a virtual environment with the
required dependencies and build an installer bundle in
bundle/edcopilot-mfd.zip or bundle/edcopilot-mfd-linux.tar.gz.

If the companion is disabled in the MFD plugin settings, it can be run
from an IDE and restarted without restarting the game.  Most of the
features can be tested without the game running using the test interface
in src/mfdclient/guiclient.py.