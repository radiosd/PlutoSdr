"""
    Using unittest to validate code for FirConfig class in pluto_fir
    Just the twos compliment stuf for now
    #It relies on having a device connected.
                                                         rgr11Aug18
    look for #!# lines where corrections are pending
"""
from __future__ import print_function

import logging

import unittest
from pluto import pluto_fir
from pluto.pluto_fir import setBit, twosC2Int, int2TwosC  # just these 3 first

class TestFirConfigClass(unittest.TestCase):

    def setUp(self):
        self.longMessage = True  # enables "test != result" in error message
##        self.ctx = iio.Context('ip:pluto.local')
##        self.dev = self.ctx.find_device('cf-ad9361-dds-core-lpc')

    def tearDown(self):
        pass

    # everything starting test is run, but in no guaranteed order
    def testControlBit(self):
        """confirm set and clear bits by index"""
        value = 0xFF
        self.assertEqual(setBit(4, value, 0), 0xEF, 'clear bit 4')
        self.assertEqual(setBit(0, value, 0), 0xFE, 'clear bit 0')
        value = 0x00
        self.assertEqual(setBit(4, value, 1), 0x10, 'set bit 4')
        self.assertEqual(setBit(0, value, 1), 0x01, 'set bit 0')
        
    def testTwosComplimentStuff(self):
        """check translation to and from twos compliment"""
        self.assertEqual(twosC2Int(255, 250), -6, 'bytes to int')
        self.assertEqual(twosC2Int(0, 6), 6, 'bytes to int')
        #!# check edge values
        self.assertTupleEqual(int2TwosC(-6), (255, 250), 'int to bytes')
        
if __name__=='__main__':
    # for now need a device connected to do tests
    from os import path
    import sys
##    try:
##        iio.Context('ip:pluto.local')   # just to find whether it is connected
##    except:
##        print('testDdsClass requires a pluto device connected')
##        sys.exit(1)
        
    # show what is being tested and from where
    print('\nTesting class FirConfig in module:\n',
          path.abspath(pluto_fir.__file__))
    
    logging.basicConfig(format='%(module)-12s.%(funcName)-12s:%(levelname)s - %(message)s',
                        stream=sys.stdout, level=logging.INFO)
    unittest.main()
