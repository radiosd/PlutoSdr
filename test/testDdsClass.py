
"""
    Using unittest to validate code for pluto_dds.Dds class
    It relies on having a device connected.
    Using mock was too troublesome 
                                                         rgr16jul18
    look for #!# lines where corrections are pending
"""
from __future__ import print_function

import logging

import unittest

# for numpy operations, there are additional assertTests in the numpy module
import numpy.testing as npt

import iio
from pluto import pluto_dds
from pluto.controls import ON, OFF

class TestDdsClass(unittest.TestCase):

    def setUp(self):
        self.longMessage = True  # enables "test != result" in error message
        self.ctx = iio.Context('ip:pluto.local')
        self.dev = self.ctx.find_device('cf-ad9361-dds-core-lpc')

    def tearDown(self):
        pass

    # everything starting test is run, but in no guaranteed order
    def testDdsCreate(self):
        """create a Dds instance"""
        self.assertIsInstance(self.dev, iio.Device, 'ok')
        dds = pluto_dds.Dds(self.dev)
        self.assertIsInstance(dds.t1, pluto_dds.DdsTone,
                          'Dds Tone1 instance created')
        self.assertIsInstance(dds.t2, pluto_dds.DdsTone,
                          'Dds Tone2 instance created')
        self.assertTrue(dds.isOff(), "initial state is both off")

    def testSetFrequency(self):
        """confirm read and write to properties"""
        dds = pluto_dds.Dds(self.dev)
        fs = dds.getSamplingFreq()    # test tones must be within +/- hald Fs    
        dds.setFrequency(fs/4)
        npt.assert_almost_equal(dds.t1.frequency, fs/4, decimal=3,
                         err_msg='set f1 frequency')
        dds.setFrequency(fs/4, -fs/8)
        npt.assert_almost_equal(dds.t1.frequency, fs/4, decimal=3,
                         err_msg='set f1 frequency')
        npt.assert_almost_equal(dds.t2.frequency, -fs/8, decimal=3,
                         err_msg='set f2 frequency')
        
    def testSetPhase(self):
        """confirm the relative I/Q phases for +/- frequencies"""
        dds = pluto_dds.Dds(self.dev)        
        tone = pluto_dds.DdsTone(self.dev, 'F1')
        tone.frequency = 1
        tone.phase = 180       # set phase mid way
        i_phase = tone.getPhase()
        q_phase = tone.getPhase('Q')

    def testSetAmplitude(self):
        """confirm amplitude values read/write and amp <= 0 dB"""
        dds = pluto_dds.Dds(self.dev)
        # dds.setAmplitude()  should be created OFF
        self.assertEqual(dds.t1.amplitude, 0,
                         'created with amplitude 1 off')
        self.assertEqual(dds.t2.amplitude, 0,
                         'created with amplitude 2 off')
        with self.assertRaises(ValueError, msg='values set in -dB '):
            dds.setAmplitude(10)
        dds.setAmplitude(-10)  # this is in dB
        npt.assert_almost_equal(dds.t1.amplitude, 0.1, decimal=3,
                         err_msg='first arguments sets f1 amplitude')
        self.assertEqual(dds.t2.amplitude, 0,
                         'no arguments turn amplitude 2 off')
        dds.setAmplitude(-13, -13)
        npt.assert_almost_equal(dds.t1.amplitude, 0.05, decimal=3,
                         err_msg='first arguments sets f1 amplitude')
        npt.assert_almost_equal(dds.t2.amplitude, 0.05, decimal=3,
                         err_msg='second arguments sets f2 amplitude')
        self.assertTrue(dds.isOff(), 'created OFF, independent of amplitude')   
        dds.state(ON);     
        self.assertFalse(dds.isOff(), 'have to explicitly turn on')
    
if __name__=='__main__':
    # for now need a device connected to do tests
    from os import path
    import sys
    try:
        iio.Context('ip:pluto.local')   # just to find whether it is connected
    except:
        print('testDdsClass requires a pluto device connected')
        sys.exit(1)
        
    # show what is being tested and from where
    print('\nTesting class Dds in module:\n',path.abspath(pluto_dds.__file__))
        
    logging.basicConfig(format='%(module)-12s.%(funcName)-12s:%(levelname)s - %(message)s',
                        stream=sys.stdout, level=logging.INFO)
    unittest.main()
    
