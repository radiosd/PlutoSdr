"""
    Using unittest to validate code for readFilter
    #It relies on having a device connected.
                                                         rgr15Aug18
    look for #!# lines where corrections are pending
"""
from __future__ import print_function

import logging

import unittest
from pluto import readFilter

TEST_FILE = 'test/LTE1p4_MHz'
# a represetative sample of data is hard coded in testFunction()
RX_TAPS = [5, -21, -51, -120, -212, -338, -471, -599]  # first and last 8
TX_TAPS = [26, 12, 14, -30, -90, -198, -323, -465]

class TestFilterRead(unittest.TestCase):

    def setUp(self):
        self.longMessage = True  # enables "test != result" in error message

    def tearDown(self):
        pass

    def testFunction(self):  # only one function really
        """confirm a sample set of data that should be read in"""
        res = readFilter.readFilter(TEST_FILE)
        self.assertEqual(res['file'], 'LTE1p4_MHz.ftr', 'correct file extension')
        self.assertEqual(res['tx_CH'], 3, 'reading ch info')

        self.assertEqual(res['rx_bw'], 1.613792, 'reading BW info')

        self.assertEqual(res['TXPLL'], 737.28, 'reading PLL info')
        self.assertEqual(res['ADC'], 92.16, 'reading ADC info')

        self.assertEqual(len(res['rx_taps']), 128, 'no of taps in rx fir')
        self.assertListEqual(res['rx_taps'][:8], RX_TAPS, 'some rx taps')
        self.assertListEqual(res['rx_taps'][-8:], 
               RX_TAPS[::-1], 'reverse symmetric rx taps at the end')

        self.assertEqual(len(res['tx_taps']), 128, 'no of taps in tx fir')
        self.assertListEqual(res['tx_taps'][:8], TX_TAPS, 'some tx taps')
        
        
if __name__=='__main__':
    # for now need a device connected to do tests
    from os import path
    import sys
    # show what is being tested and from where
    print('\nTesting class FilterRead in pluto.filterRead:\n',
          path.abspath(readFilter.__file__))
    
    logging.basicConfig(
        format='%(module)-12s.%(funcName)-12s:%(levelname)s - %(message)s',
        stream=sys.stdout, level=logging.ERROR)
    unittest.main()
