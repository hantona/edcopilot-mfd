import logging
import re
from typing import Any

from data.outfittingprices import outfitting_prices
from data.armorprices import armor_prices

# Look up equipment prices in a copy standard prices from Inara
# The Inara price list groups similar items together
# To avoid needing to manipulate the exported data, the code transforms the name from EDCopilot to match the data


price_lookup_log = logging.getLogger("price_lookup")
# Map from letter words used for EDCopilot item quality to the letter
letters = {"Alpha": "A",
           "Bravo": "B",
           "Charlie": "C",
           "Delta": "D",
           "Echo": "E",
           "Foxtrot": "F",
           "Golf": "G",
           "Hotel": "H",
           "India": "I"}

# Items starting with these names are considered to be quality variants of the item without the prefix
# They need to be removed from the item name before the initial lookup in the Inara data
inara_condensed_prefixes = ["Advanced ", "Large ", "Mk II Large ", "MKII Large ", "MERC ", "Enhanced ", "Sirius ",
                            "Azimuth enhanced ", "Modified ", "Mk II Shock ", "Engineered ", "MERC Drag ",
                            "MERC Exposing ", "MERC Lightweight ", "MERC Lockdown ", "Mk II ",
                            "Mk II Supercharge Optimised ", "Enhanced Performance ", "Mk II Agile ",
                            "Mk II Gravity Optimised ", ]


# Mapping from name to Inara name when prefix stripping can't be used without breaking another item
inara_name_fixup = {
    "Pulse Wave Xeno Scanner": "Xeno Scanner"
}


def find_price(part_name, quality, ship):
    """Find the price for a component that may be armor"""
    price = find_armor_price(part_name, ship)

    if not price:
        price = find_component_price(part_name, quality)

    return price


def find_component_price(part_name, quality):
    """Find the price for a non-armor component"""
    price = None
    inara_part_name = transform_name(part_name)
    inara_quality_name = transform_quality(part_name, quality)

    if inara_part_name in outfitting_prices:
        part_prices = outfitting_prices[inara_part_name]
        if inara_quality_name in part_prices:
            price = part_prices[inara_quality_name]

    if price is None:
        price_lookup_log.error(f"Failed to find price for {part_name} with quality {quality}")
        price_lookup_log.debug((f"The name and quality were transformed to {inara_part_name} "
                                f"and {inara_quality_name} for lookup in the price data"))

    return price


def transform_name(part_name) -> Any:
    """Transform the part name from EDCoPilot to match what is used by Inara"""
    inara_part_name = part_name

    # Check the prefixes in descending order of size to find 'Mk II Large ' before 'Mk II '
    prefixes_by_length = sorted(inara_condensed_prefixes, key=lambda x: len(x), reverse=True)

    for prefix in prefixes_by_length:
        if part_name.startswith(prefix):
            inara_part_name = inara_part_name.replace(prefix, "")
            break

    if part_name in inara_name_fixup:
        inara_part_name = inara_name_fixup[part_name]
    return inara_part_name


def transform_quality(part_name, quality) -> str | None:
    """Transform the quality displayed in EDCoPilot to match what is used by Inara"""
    quality_match = re.match("([0-9]) ([^ ]*) ?([^ ]*)?", quality)
    inara_quality_name = None

    if quality_match:
        size = quality_match.group(1)
        quality = quality_match.group(2)
        if quality in letters:
            quality = letters[quality]

        inara_quality_name = size + quality
        inara_quality_name += " " + part_name

        if quality_match.group(3):
            hardpoint_type = quality_match.group(3)
            inara_quality_name += f" [{hardpoint_type}]"
    return inara_quality_name


def find_armor_price(part_name, ship):
    """Find the armor price for a specific ship"""
    price = None

    if part_name in armor_prices:
        if ship in armor_prices[part_name]:
            price = armor_prices[part_name][ship]

    return price
