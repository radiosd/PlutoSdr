
"""
    Using unittest to validate code for pluto_dds.DdsTone
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

class TestDdsTone(unittest.TestCase):

    def setUp(self):
        self.longMessage = True  # enables "test != result" in error message
        self.ctx = iio.Context('ip:pluto.local')
        self.dev = self.ctx.find_device('cf-ad9361-dds-core-lpc')

    def tearDown(self):
        pass

    # everything starting test is run, but in no guaranteed order
    def testToneCreate(self):
        """create a Dds with a DdsTone instance"""
        self.assertIsInstance(self.dev, iio.Device, 'ok')
        tone = pluto_dds.DdsTone(self.dev, 'F1')
        self.assertIsInstance(tone, pluto_dds.DdsTone,
                          'ddsTone instance created')
        tone.setFreq(1)
        npt.assert_almost_equal(tone.getFreq(), 1.0, decimal=4,
                         err_msg='initial frequency value')
        tone.setPhase(0)
        npt.assert_almost_equal(tone.getPhase(), 0.0, decimal=4,
                         err_msg='initial phase value')
        npt.assert_almost_equal(tone.getPhase('Q'), 270.0, decimal=4,
                         err_msg='initial phase value')
        tone.setAmplitude(0.5)
        npt.assert_almost_equal(tone.getAmplitude(), 0.5, decimal=4,
                         err_msg='initial amplitude value')

    def testProperties(self):
        """confirm read and write to properties"""
        tone = pluto_dds.DdsTone(self.dev, 'F1')
        fs = tone.getSamplingFreq()        
        tone.frequency = -fs/4
        npt.assert_almost_equal(tone.frequency, -fs/4, decimal=3,
                         err_msg='using frequency property')
        tone.phase = 20
        npt.assert_almost_equal(tone.phase, 20.0, decimal=3,
                         err_msg='using phase property')
        tone.amplitude = 0.2
        npt.assert_almost_equal(tone.amplitude, 0.2, decimal=3,
                         err_msg='using amplitude property')
        with self.assertRaises(ValueError,

                    msg='value set out of 0 .. 1 range'):
            tone.amplitude = 10
        
    def testPosNegFreq(self):
        """confirm the relative I/Q phases for +/- frequencies"""
        tone = pluto_dds.DdsTone(self.dev, 'F1')
        fs = tone.getSamplingFreq()        
        tone.frequency = fs/8
        tone.phase = 180       # set phase mid way
        i_phase = tone.getPhase()
        q_phase = tone.getPhase('Q')
        tone.frequency = -fs/4
        self.assertEqual(i_phase, tone.getPhase(),
                         'I phase equal for +/- freq')
        self.assertEqual(abs(q_phase - tone.getPhase('Q')), 180,
                         'Q phase opposite for +/- freq')

    def testOnOff(self):
        """confirm amplitude settings are preserved from off to on"""
        tone = pluto_dds.DdsTone(self.dev, 'F1')
        tone.amplitude = 0.5   # some initial setting
        self.assertEqual(tone.amplitude, 0.5, "setting attribute ok")
        tone.state(OFF)
        self.assertEqual(tone.amplitude, 0.0, "off make amplitude 0")
        tone.state(ON)
        self.assertEqual(tone.amplitude, 0.5, "return to previous setting")
        tone.state(OFF)
        tone.amplitude = 0.1
        tone.state(ON)
        npt.assert_almost_equal(tone.amplitude, 0.1, decimal=4,
                                err_msg="ok setting change even when off")

    def testPhaseNormalisation(self):
        """confirm phase values restricted to 0 <= phi <= 360"""
        tone = pluto_dds.DdsTone(self.dev, 'F1')
        tone.phase = -10
        npt.assert_almost_equal(tone.phase, 350, decimal=2,
                         err_msg='phase norm -10 -> 350 degs')

    def testWithinFs(self):
        """confirm freq values are within +/- half fs"""
        tone = pluto_dds.DdsTone(self.dev, 'F1')
        tone.amplitude = 0.5
        tone.frequency = 0.5
        fs = tone.getSamplingFreq() 
        with self.assertRaises(ValueError,
                msg='when setting f outside +/-fs/2'):  
            tone.setFreq(fs)
                        
if __name__=='__main__':
    from os import path
    import sys
    # tests require a device to be connected
    try:
        iio.Context('ip:pluto.local')   # just to find whether it is connected
    except:
        print('testDdsTone requires a pluto device connected')
        sys.exit(1)

    # show what is being tested and from where 
    print('\nTesting class DdsTone in module:\n',path.abspath(pluto_dds.__file__))


    logging.basicConfig(format='%(module)-12s.%(funcName)-12s:%(levelname)s - %(message)s',
                        stream=sys.stdout, level=logging.INFO)
    
    unittest.main()
       
