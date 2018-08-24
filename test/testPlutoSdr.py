
"""
    Using unittest to validate code for pluto_sdr
    It relies on having a device connected. But ncanot validate RF control
                                                         rgr29jul18
    look for #!# lines where corrections are pending
"""
from __future__ import print_function

import logging

import unittest

# for numpy operations, there are additional assertTests in the numpy module
import numpy.testing as npt

import iio
from pluto import pluto_sdr
from pluto.controls import ON, OFF

class TestplutoSdr(unittest.TestCase):

    def setUp(self):
        self.longMessage = True  # enables "test != result" in error message
        self.sdr = pluto_sdr.PlutoSdr('ip:pluto.local')

    def tearDown(self):
        pass

    # everything starting test is run, but in no guaranteed order
    def testPlutoSdrCreate(self):
        """create a PlutoSdr instance"""
        self.assertIsInstance(self.sdr.ctx, iio.Context, 'ok')

    def testSysAttributes(self):
        """confirm read and write to system properties"""
        sdr = self.sdr
        fs = sdr.sampling_frequency
        sdr.sampling_frequency = 10     # set in MHz
        self.assertEqual(sdr.sampling_frequency, 10.0, 'Fs set in MHz')
        sdr.sampling_frequency = fs
        self.assertEqual(sdr.sampling_frequency, fs, 're-set to original')

    def testRxAttributes(self):
        """confirm read and write to rx properties"""
        sdr = self.sdr
        fs = sdr.sampling_frequency
        decimate = sdr.rx_decimation
        sdr.rx_decimation = True
##        self.assertEqual(sdr.rxBBSampling(), fs, 'decimation  off')
        self.assertEqual(sdr.rxBBSampling(), fs/8, 'decimation on')
        sdr.rx_decimation = decimate      
        bw = sdr.rx_bandwidth        # this is the turn on value
        sdr.rx_bandwidth = 12.2      # set in MHz
        self.assertEqual(sdr.rx_bandwidth, 12.2, 'BW set in MHz')
        sdr.rx_bandwidth = bw
        self.assertEqual(sdr.rx_bandwidth, bw, 're-set to original BW')
        # some values are truncated due to available synth settings
        #!# no check on an out of range value        
        lo = sdr.rx_lo_freq          # this is the turn on value
        sdr.rx_lo_freq = 430.1       # set in MHz 
        npt.assert_almost_equal(sdr.rx_lo_freq, 430.1, decimal=6,
                             err_msg='setting rx lo in MHz')
        sdr.rx_lo_freq = lo
        npt.assert_almost_equal(sdr.rx_lo_freq, lo, decimal=6,
                             err_msg='re-set to original LO')
        gain = sdr.rx_gain
        sdr.rx_gain = 20.0     # set value in dB
        self.assertEqual(sdr.rx_gain, 20.0, 'gain set in dB')
        sdr.rx_gain = gain
        self.assertEqual(sdr.rx_gain, gain, 're-set to original gain')
        
    def testTxAttributes(self):
        """confirm read and write to tx properties"""
        sdr = self.sdr
        fs = sdr.sampling_frequency
        interpolate = sdr.tx_interpolation
        sdr.tx_interpolation = True
        self.assertEqual(sdr.txBBSampling(), fs/8, 'interpolation on')
        sdr.interpolation = interpolate
        bw = sdr.tx_bandwidth      # this is the turn on value
        sdr.tx_bandwidth = 10.2    # set in MHz
        self.assertEqual(sdr.tx_bandwidth, 10.2, 'BW set in MHz')
        sdr.tx_bandwidth = bw
        self.assertEqual(sdr.tx_bandwidth, bw, 're-set to original BW')
        lo = sdr.tx_lo_freq          # this is the turn on value
        sdr.tx_lo_freq = 330.1       # set in MHz 
        npt.assert_almost_equal(sdr.tx_lo_freq, 330.1, decimal=6,
                             err_msg='setting tx lo in MHz')
        sdr.tx_lo_freq = lo
        npt.assert_almost_equal(sdr.tx_lo_freq, lo, decimal=6,
                             err_msg='re-set to original LO')
        gain = sdr.tx_gain
        sdr.tx_gain = -20     # set value in dB
        self.assertEqual(sdr.tx_gain, -20, 'gain set in (neg) dB')
        sdr.tx_gain = gain
        self.assertEqual(sdr.tx_gain, gain, 're-set to original gain')

    def testDdsControl(self):
        """confirm higher level control of DDS"""
        sdr = self.sdr
        state = sdr.dds.isOff()
        sdr.ddsState(OFF)
        self.assertTrue(sdr.dds.isOff(), 'dds off from sdr function')
        sdr.ddsState(ON)        # on with 0 amplituide is still off
        sdr.dds.setAmplitude(-1, -1)   # set some level
        self.assertFalse(sdr.dds.isOff(), 'dds on from sdr function')
        npt.assert_almost_equal(sdr.dds.t1.amplitude, 10**(-1.0/10), decimal=4,
                               err_msg='t1 amplitude set correctly')
        npt.assert_almost_equal(sdr.dds.t2.amplitude, 10**(-1.0/10), decimal=4,
                               err_msg='t2 amplitude set correctly')
        sdr.ddsState(state)
    
if __name__=='__main__':
    # for now need a device connected to do tests
    from os import path
    import sys
    try:
        iio.Context('ip:pluto.local')   # just to find whether it is connected
    except:
        print('testPlutoSdr requires a pluto device connected')
        sys.exit(1)
        
    # show what is being tested and from where
    print('\nTesting class plutoSdr in module:\n',path.abspath(pluto_sdr.__file__))
        
    logging.basicConfig(
        format='%(module)-12s.%(funcName)-12s:%(levelname)s - %(message)s',
        stream=sys.stdout, level=logging.INFO)
    class LogFilter(logging.Filter):
        def __init__(self, module):
            self.module = module
            
        def filter(self, record):
            return path.basename(record.pathname)==self.module
        
    logging.root.addFilter(LogFilter('pluto_sdr.py'))
    unittest.main()
    
