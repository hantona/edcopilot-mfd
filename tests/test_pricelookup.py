import unittest

import pricelookup


class PriceLookupTestCase(unittest.TestCase):
    def test_price_lookup(self):
        price = pricelookup.find_price("Beam Laser", "1 Echo Gimballed", "Anaconda")
        self.assertEqual("74,650 Cr", price)

        price = pricelookup.find_price("Beam Laser", "1 Echo Fixed", "Anaconda")
        self.assertEqual("37,430 Cr", price)

        price = pricelookup.find_price("Manifest Scanner", "0 Alpha", "Anaconda")
        self.assertEqual("1,097,100 Cr", price)

        price = pricelookup.find_price("Advanced Plasma Accelerator", "3 Bravo Fixed", "Anaconda")
        self.assertEqual("4,576,800 Cr", price)

        price = pricelookup.find_price("Military Grade Composite", "", "Anaconda")
        self.assertEqual("132,272,510 Cr", price)

        price = pricelookup.find_price("Mk II Ablative Reinforced Alloy", "", "Caspian Explorer")
        self.assertEqual("77,944,515 Cr", price)

        price = pricelookup.find_price("Large Planetary Vehicle Hangar", "6 Foxtrot", "Anaconda")
        self.assertEqual("1,036,800 Cr", price)

        price = pricelookup.find_price("Mk II Large Planetary Vehicle Hangar", "6 Foxtrot", "Anaconda")
        self.assertEqual("1,036,800 Cr", price)

        price = pricelookup.find_price("Pulse Wave Xeno Scanner", "0 Charlie", "Anaconda")
        self.assertEqual("850,000 Cr", price)


if __name__ == '__main__':
    unittest.main()
