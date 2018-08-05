"""
   Tools to access dds device in pluto

                                                          rgr15jul18
"""
from __future__ import print_function

import logging

from math import copysign, log10
from pluto import iio_lambdas as iiol
from pluto.controls import ON, OFF

class DdsTone(object):
    def __init__(self, owner, name):
        self.i_ch = owner.find_channel('TX1_I_'+ name)
        self.q_ch = owner.find_channel('TX1_Q_'+ name)
        self.amplitude = 0   # initially off
        self._freq = 0
        self._phase = 0

    def getSamplingFreq(self):
        """convenience function for testing the valid range for setFreq"""
        return iiol._Str2M(self.i_ch.attrs['sampling_frequency'].value)

    def getFreq(self):
        """get the actual frequency set in MHz with I/Q phase giving +/-"""
        i_phase = self.getPhase()
        q_phase = self.getPhase('Q')
        f = iiol._Str2M(self.i_ch.attrs['frequency'].value)
        if iiol._PNorm(i_phase - q_phase)<180:
            return f
        else:
            return -f

    def setFreq(self, f):
        """set to approximately the frequency given in MHz"""
        # approx because the actual freq is constrained by the algorithm
        # read back from the device to determine the actual value set
        self._freq = f
        # must be 0 <= f < fs/2
        if abs(f)>self.getSamplingFreq()/2:
            half_fs = '{:2.3f}'.format(self.getSamplingFreq()/2)
            raise ValueError('frequency not within +/-Fs/2 i.e '+half_fs+'MHz')
        # for positive frequencies phase(Q) = phase(I) - 90
        # for negative frequencies abs(f) and phase(Q) = phase(I) + 90
        logging.debug('freq:>' + iiol._M2Str(f))
        self.__setFreq()
        self.__setPhase()

    def __setFreq(self):
        self.i_ch.attrs['frequency'].value = iiol._M2Str(abs(self._freq))
        # read back the actual value
        self._freq = copysign(self.getFreq(), self._freq)
        logging.debug('i_ch:< '+iiol._M2Str(abs(self._freq))) 
        self.q_ch.attrs['frequency'].value = iiol._M2Str(abs(self._freq))
        logging.debug('q_ch:< '+iiol._M2Str(abs(self._freq))) 
    frequency = property(getFreq, setFreq)

    def getPhase(self, ch='I'):
        """get the actual phase set in degs"""
        if ch.upper()=='I':
            return iiol._Str2P(self.i_ch.attrs['phase'].value)
        else:
            return iiol._Str2P(self.q_ch.attrs['phase'].value)

    def setPhase(self, phi):
        """set the phase given in degrees"""
        # 0 <= phi < 360 
        self._phase = iiol._PNorm(phi)  # silent error, PNorm resolves it
        logging.debug('phase:> ' + str(int(round(phi,3)*1000))+'->'+
                      str(int(round(self._phase,3)*1000)))
        self.__setPhase()
        self.__setFreq()

    def __setPhase(self):
        self.i_ch.attrs['phase'].value = iiol._P2Str(self._phase)
        # read back the actual value
        self._phase = self.getPhase()
        logging.debug('i_ch:< '+iiol._P2Str(self._phase))
        ph2 = iiol._PNorm(self._phase - copysign(90, self._freq))
        self.q_ch.attrs['phase'].value = iiol._P2Str(ph2)
        logging.debug('q_ch:< '+iiol._P2Str(ph2))
    phase = property(getPhase, setPhase)

    def getAmplitude(self):
        """get the actual amplitude set in dBs"""
        return iiol._Str2A(self.i_ch.attrs['scale'].value)

    def setAmplitude(self, amp):
        """set the amplitude given with  0 <= amp <= 1"""
        if amp<0 or amp>1:
            raise ValueError('amplitude must be positive and unity maximum')
        self._amp = amp
        self._setAmplitude(amp)

    def _setAmplitude(self, amp):
        logging.debug('amp:>'+'{:1.6f}'.format(round(amp,6)))
        self.i_ch.attrs['scale'].value = '{:1.6f}'.format(round(amp,6))
        self.q_ch.attrs['scale'].value = '{:1.6f}'.format(round(amp,6))
    amplitude = property(getAmplitude, setAmplitude)

    def state(self, value):
        """control the on/off state of the tone"""
        if value==OFF:
            logging.debug('off')
            self._amp = self.amplitude
            self._setAmplitude(0)
        else:
            logging.debug('on')
            self.amplitude = self._amp
        
    def status(self):
        return (self.amplitude, self.frequency, self.phase)

    def _showCh(self, iq):
        if iq.upper()=='I':
            ch = self.i_ch.attrs
        else:
            ch = self.q_ch.attrs
        print('{:s} {:s} {:s} {:s}'.format(iq.upper(),
               ch['scale'].value, ch['frequency'].value, ch['phase'].value))

    def showTone(self):
        """ ... """
        self._showCh('I')
        self._showCh('Q')
        
class Dds(object):
    def __init__(self, dev):
        self.device = dev
        logging.debug('create Dds instance')
        self.t1 = DdsTone(dev, 'F1')
        self.t2 = DdsTone(dev, 'F2')
        # initialise with both off
        self.setAmplitude()
##        self.t1_amplitude = 0  # this should now be obsolete
##        self.t2_amplitude = 0

    def getSamplingFreq(self):
        """return the sampling freq in MHz. Read only"""
        return self.t1.getSamplingFreq()

    def setAmplitude(self, amp1=None, amp2=None):
        """set amplitude of the tones in dB, default None turns off """
        if amp1 is None:
            self.t1.setAmplitude(0)
        elif amp1<=0:
            self.t1.amplitude = 10**(amp1/10.0)
        else:
            raise ValueError('tone amplitudes set in -dB levels')
        if amp2 is None:
            self.t2.setAmplitude(0)
        elif amp2<=0:
            self.t2.amplitude = 10**(amp2/10.0)
        else:
            raise ValueError('tone amplitudes set in -dB levels')

    def setFrequency(self, f1, f2=None):
        self.t1.setFreq(f1)
        if f2 is not None:
            self.t2.setFreq(f2)
        
    def setPhase(self, ph1, ph2=None):
        self.t1.setPhase(ph1)
        if ph2 is not None:
            self.t2.setphase(ph2)

    def isOff(self):
        return self.t1.amplitude==0 and self.t1.amplitude==0
    
    def status(self, tone=1):
        tone = self.t1 if tone==1 else  self.t2
        amp = 99.9 if tone.amplitude==0 else tone.amplitude
        return (tone.frequency, 'MHz', tone.phase, 10*log10(amp),'dBFS')

if __name__=='__main__':
    import sys
    import iio
    logging.basicConfig(format='%(module)-12s.%(funcName)-12s:%(levelname)s - %(message)s',
                        stream=sys.stdout, level=logging.DEBUG)
    try:
        ctx = iio.Context('ip:pluto.local')
        dds = ctx.find_device('cf-ad9361-dds-core-lpc')
        t1 = DdsTone(dds, 'F1')
    except:
        # warning: more than 1 thing can go wrong!!
        print('requires a pluto to be connected')
