"""
    Basic class to simplifiy interaction with pluto as an iio device
                                                            rgr12jan18
 * Copyright (C) 2018 Radio System Desing Ltd.
 * Author: Richard G. Ranson, richard@radiosystemdesign.com
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation under
 * version 2.1 of the License.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
"""
# basic class to simplifiy interaction with pluto as an iio device
from __future__ import print_function

import logging

import iio
import numpy as np

PLUTO_ID = 'ip:pluto.local'
NO_BITS = 12                      # internal ADC and DAC width

# properties are in MHz, but the value set is a str
from pluto.iio_lambdas import _M2Str

from pluto import pluto_dds
from pluto.controls import devFind, ON, OFF, FLOAT, COMPLEX

class PlutoSdr(object):
    """Encapsulation of Pluto SDR device
       iio lib interface used to expose common functionality"""
    # nothing to force this to be a singleton - it would make sense to do that
    # however, multiples do seem to exists without conflict
    no_bits = NO_BITS
    def __init__(self, uri=PLUTO_ID):
        # access to internal devices
        try:
            self.ctx = iio.Context(uri)
        except FileNotFoundError:
            print('exception: no iio device context found at',uri)
            return
        logging.debug('found context for pluto device')
        self.name = 'plutosdr'
        self.phy = devFind(self.ctx, 'ad9361-phy')
        # individual TRx controls
        self.phy_rx = self.phy.find_channel('voltage0', is_output=False)
        self.phy_tx = self.phy.find_channel('voltage0', is_output=True)
        # access to data channels for Rx
        self.adc = devFind(self.ctx, 'cf-ad9361-lpc')
        # access to data channels for Tx
        self.dac = devFind(self.ctx, 'cf-ad9361-dds-core-lpc')
        self.tx_channels = [self.dac.find_channel('voltage0', True)]
        self.tx_channels.append(self.dac.find_channel('voltage1', True))        
        # also access to the internal 2 tone generator
        self.dds = pluato_dds.Dds(self.dac)
        #  tx buffer, created in writeTx and retained for continuous output 
        self._tx_buff = None
    # ----------------- TRx Physical Layer controls -----------------------
    def _get_SamplingFreq(self):
        """internal ADC sampling frequency in MHz"""
        # available from many channel none of which are named
        # changes to [4] seem to alter them all
        value = self.phy_rx.attrs['sampling_frequency'].value
        return int(value)/1e6

    def _set_SamplingFreq(self, value):
        self.phy_rx.attrs['sampling_frequency'].value = _M2Str(value)

    sampling_frequency = property(_get_SamplingFreq, _set_SamplingFreq)

    def rxSynth(self):
        # read only always
        values = [x.split(':')\
                  for x in self.phy.attrs['rx_path_rates'].value.split(' ')]
        in_mhz = [(x[0], int(x[1])/1e6) for x in values]
        return dict(in_mhz)

    def txSynth(self):
        # read only always
        values = [x.split(':')\
                  for x in self.phy.attrs['tx_path_rates'].value.split(' ')]
        in_mhz = [(x[0], int(x[1])/1e6) for x in values]
        return dict(in_mhz)
        
    def loopBack(self, enable):   # not yet used or tested
        """turn loop-back function on/off"""
        self.phy.debug_attrs['loop_back'].value = enable

    # ---------------------- Receiver control-------------------------
    # property actual value may be slightly different because the
    # firmware converts them to available value from the synth
    def rxStatus(self):
        """print the key parameters for the receive signal chain"""
        print('Rx Fs:{:2.1f}MHz    BB: {:7.2f}MHz'\
              .format(self.sampling_frequency, self.rxBBSampling()))
        print('   BW:{:2.1f}MHz    LO: {:7.2f}MHz'\
              .format(self.rx_bandwidth, self.rx_lo_freq))
        print(' Gain:{:2.1f}dB   Mode: {:s}'\
              .format(self.rx_gain, self.phy_rx.attrs['gain_control_mode'].value))

    def rxBBSampling(self):
        """the rx base band sampling rate in MHz"""
        fs = self.sampling_frequency
        return fs/8 if self.rx_decimation else fs
##        return float(self.adc.channels[0].attrs['sampling_frequency'].value)/1e6
        
    def _get_rxDownSampling(self):
        """control receiver output sampling frequency in MHz"""
        # only 2 options adc_rate or adc_rate/8
        _adc = self.adc.channels[0].attrs
        value = _adc['sampling_frequency'].value
        options = _adc['sampling_frequency_available'].value.split(' ')
        logging.debug('get: rx_decimation:<' + value)
        return value==options[1]
            
    def _set_rxDownSampling(self, enable):
        if isinstance(enable, bool) or isinstance(enable, int):
            _adc = self.adc.channels[0].attrs
            options = _adc['sampling_frequency_available'].value.split(' ')
            _adc['sampling_frequency'].value = options[enable]
            logging.debug('set: rx_decimation:>' + str(options[enable]))
        else:
            raise ValueError('bool expected: only 2 options for rx_sampling')
        
    rx_decimation = property(_get_rxDownSampling, _set_rxDownSampling)

    def _get_rxLoFreq(self):
        """receiver LO frequency property in MHz"""
        value = self.phy.find_channel('RX_LO').attrs['frequency'].value
        return int(value)/1e6

    def _set_rxLoFreq(self, value):
        self.phy.find_channel('RX_LO').attrs['frequency'].value = _M2Str(value)
        
    rx_lo_freq = property(_get_rxLoFreq, _set_rxLoFreq)
    
    def _get_rxBW(self):
        """receiver analogue RF bandwidth in MHz"""
        # available from channel [4] or [5] which are not named
        # iio-scope only changes [4], so use that 
        value = self.phy_rx.attrs['rf_bandwidth'].value
        return int(value)/1e6

    def _set_rxBW(self, value):
        self.phy_rx.attrs['rf_bandwidth'].value = _M2Str(value)
        
    rx_bandwidth = property(_get_rxBW, _set_rxBW, doc='RF bandwidth of rx path')
        
    def _get_rx_gain(self):
        """read the rx RF gain in dB"""
        value = self.phy_rx.attrs['hardwaregain'].value.split(' ')
        return float(value[0])

    # to set rx gain need to also control the gain mode
    def _set_rx_gain(self, value=None):
        """set the rx RF gain in dB or to auto, slow attack"""
        if value is None:
            print('mode set to "slow_attack", other controls not yet available')
            self.phy_rx.attrs['gain_control_mode']\
                                       .value = 'slow_attack'
        else:
            self.phy_rx.attrs['gain_control_mode'].value = 'manual'
            self.phy_rx.attrs['hardwaregain']\
                                       .value = '{:2.3f} dB'.format(value)
            
    rx_gain = property(_get_rx_gain, _set_rx_gain)

    def _set_rx_gain_mode(self, mode):
        avail = self.phy_rx.attrs['gain_control_mode_available'].value
        options = avail.split()
        opts = [av[0].upper() for av in options]
        if mode[0].upper() in opts:
            print('set:', options[opts.index(mode[0])])
        else:
            print('modes are:', avail.title())
    
    def _get_rx_gain_mode(self, mode):
        pass
    rx_gain_mode = property(_get_rx_gain_mode, _set_rx_gain_mode)
    
    # getting data from the rx  
    def _get_rx_data(self):
        self._adc_iio_buffer.refill()
        return self._adc_iio_buffer.read()
       
    def readRx(self, no_samples, raw=True):
        # enable the channels
        for ch in self.adc.channels:
            ch.enabled = True
        try:  # create a buffer of the right size to use
            buff = iio.Buffer(self.adc, no_samples)
            buff.refill()
            buffer = buff.read() 
            iq = np.frombuffer(buffer, np.int16)  
        except OSError:
            for ch in self.adc.channels:
                ch.enabled = True
            raise OSError('failed to create iio buffer')
        if raw:
            return iq 
        else:
            return self.raw2complex(iq)

    def raw2complex(self, data):
        """return a scaled complex float version of the raw data"""
        # convert to float64, view performs an in place recast of the data
        # from SO 5658047
        # are the #bits available from some debug attr?
        # scale for 11 bits (signed 12)
        iq = 2**-(self.no_bits-1)*data.astype(FLOAT)
        return iq.view(COMPLEX)
    
    def capture(self, no_samples=0x4000, raw=False, desc=''):
        """read data from the rx and save with other RF params in a dict"""
        ans = {'desc':desc}
        ans['fs'] = self.rx_sampling_frequency
        ans['fc'] = self.rx_lo_freq
        ans['rx_bw'] = self.rx_bandwidth
        ans['rx_gain'] = self.rx_gain
        ans['data'] = self.readRx(no_samples, raw=raw)
        # for raw data the device must provide the no of bits
        if raw:                     
            ans['bits'] = self.no_bits   
        return ans              
    # -------------------- Transmitter control------------------------
    def txStatus(self, show_dds=False):
        """print the key parameters for the receive signal chain"""
        print('Tx Fs:{:5.1f}MHz    BB: {:7.2f}MHz'\
              .format(self.sampling_frequency, self.txBBSampling()))
        print('   BW:{:5.1f}MHz    LO: {:7.2f}MHz'\
              .format(self.tx_bandwidth, self.tx_lo_freq))
        state = 'off' if self._tx_buff is None else 'on'
        print(' Gain:{:4.1f}dB state: {:s}'\
              .format(self.tx_gain, state))
        if show_dds:
            if self.dds.isOff():
                print('  dds: off')
            else:
                fmt = ' dds{:n}: {:5.3f}V  {: 5.3f}MHz  {:5.2f}degs'
                print(fmt.format(1, *(self.dds.t1.status())))
                print(fmt.format(2, *(self.dds.t2.status())))

    def txBBSampling(self):
        """the base band sampling rate in MHz"""
        fs = self.sampling_frequency
        return fs/8 if self.tx_interpolation else fs
    
    def _get_txUpSampling(self):
        """control receiver output sampling frequency in MHz"""
        # only 2 options adc_rate or adc_rate/8
        _dac = self.tx_channels[0].attrs
        value = _dac['sampling_frequency'].value
        options = _dac['sampling_frequency_available'].value.split(' ')
        logging.debug('get: tx_decimation:<' + value)
        return value==options[1]
            
    def _set_txUpSampling(self, enable):
        if isinstance(enable, bool) or isinstance(enable, int):
            _dac = self.tx_channels[0].attrs
            options = _dac['sampling_frequency_available'].value.split(' ')
            _dac['sampling_frequency'].value = options[enable]
            logging.debug('set: tx_decimation:>' + str(options[enable]))
        else:
            raise ValueError('bool expected: only 2 options for tx_sampling')

    tx_interpolation = property(_get_txUpSampling, _set_txUpSampling)

    def _get_txLoFreq(self):
        """transmitterer LO frequency property in MHz"""
        value = self.phy.find_channel('TX_LO').attrs['frequency'].value
        return int(value)/1e6

    def _set_txLoFreq(self, value):
        self.phy.find_channel('TX_LO').attrs['frequency'].value = _M2Str(value)

    tx_lo_freq = property(_get_txLoFreq, _set_txLoFreq)
    
    def _get_tx_gain(self):
        """get the tx RF gain in dB, it is always neg as an attenuation"""
        value = self.phy_tx.attrs['hardwaregain'].value
        return float(value.split()[0])

    def _set_tx_gain(self, value):
        """set the tx RF gain in dB"""
        if value>0:
            raise(ValueError, 'tx gain is an attenuation, so always negative')
        self.phy_tx.attrs['hardwaregain']\
                                  .value = '{:2.3f} dB'.format(value)
        
    tx_gain = property(_get_tx_gain, _set_tx_gain)
    
    def _get_txBW(self):
        """transmitter analogue RF bandwidth in MHz"""
        # available from channel [4] or [5] which are not named
        # iio-scope only changes [5], so use that 
        value = self.phy_tx.attrs['rf_bandwidth'].value
        return int(value)/1e6

    def _set_txBW(self, value):
        self.phy_tx.attrs['rf_bandwidth'].value = _M2Str(value)

    tx_bandwidth = property(_get_txBW, _set_txBW)

    def complex2raw(self, data, no_bits):
        iq = np.round((2**(no_bits-1))*data.view(FLOAT)).astype(np.int16)
        return iq
    
    def writeTx(self, samples, raw=False):
        """write to the Tx buffer and make it cyclic"""
        if self._tx_buff is not None:
            self._tx_buff = None               # turn off any previous signal
        if isinstance(samples, bool) or len(samples)==0:          
            logging.debug('tx: off')           # leave with transmitter off
            return
        if raw:
            data = samples<<4         # align 12 bit raw to msb
        else:   # samples some are from some DiscreteSignalSource, so
                # data is complex IQ and scaled to +/-1.0 float range
                # use 16 **not** self.no_bits to align data to msb
            data = self.complex2raw(samples, 16)
        no_samples = len(data)//2
        for ch in self.tx_channels:   # enable the tx channels
            ch.enabled = True
        try:  # create a cyclic iio buffer for continuous tx output
            self._tx_buff = iio.Buffer(self.dac, no_samples//2, True)
            count = self._tx_buff.write(data)
            logging.debug(str(count)+' samples transmitted')
            self._tx_buff.push()
        except OSError:
            for ch in chs:
                ch.enabled = False
            self._tx_buff = None
            raise OSError('failed to create an iio buffer')
        # buffer retained after a successful call
        return count # just for now

    def txOutputFreq(self):
        # read only for now - confused as to which one is the controlling value
        # look at the various possibilities
        dac = self.dac
        various = {}
        various['TX1_I_F1'] = dac.channels[0].attrs['sampling_frequency'].value
        various['TX1_I_F2'] = dac.channels[1].attrs['sampling_frequency'].value
        various['TX1_Q_F1'] = dac.channels[2].attrs['sampling_frequency'].value
        various['TX1_Q_F2'] = dac.channels[3].attrs['sampling_frequency'].value       

        various['volt0'] = dac.channels[4].attrs['sampling_frequency'].value
        various['volt1'] = dac.channels[5].attrs['sampling_frequency'].value     
        return various
    # ------------------------ DDS Control ---------------------------
    def ddsState(self, value):
        """turn the dds signal(s) on/off"""
        if value==OFF:
            self.dds.t1.state(OFF)
            self.dds.t2.state(OFF)
        else:
            self.dds.t1.state(ON)
            self.dds.t2.state(ON)
        
    def ddsAmplitude(self, amp1, amp2=None):
        """control the DDS output level in dB"""
        self.dds.setAmplitude(amp1, amp2)

    def ddsFrequ(self, f1, f2=None):
        """control the DDS output level"""
        self.dds.setFrequency(f1, f2)

    def ddsPhase(self, ph1, ph2):
        self.dds.setPhase(phi, phi2)

    def ddsStatus(self):
        """show a summary of the dds system"""
        state = 'off' if self.dds.isOff() else 'on'
        print('dds:',state)
        if state=='on':
            fmt = ' dds{:n}: {:5.3f}V  {: 5.3f}MHz  {:5.2f}degs'
            print(fmt.format(1, *(self.dds.t1.status())))
            print(fmt.format(2, *(self.dds.t2.status())))

if __name__=='__main__':
    pp = PlutoSdr(PLUTO_ID)
    pp.tx_lo_freq = 430
    pp.rx_lo_freq = 430
    pp.sampling_frequency = 10

    def _sampling(ch):
        return float(ch.attrs['sampling_frequency'].value)/1e6

    def _available(ch):
        ans = [float(v)/1e6 for v in
               ch.attrs['sampling_frequency_available'].value.split()]
        return ans

    def fittedSin(no_samples, no_cycles):
        """Exact no_cycles in the sample length"""
        nn = np.arange(no_samples)
        si = np.sin(2*np.pi*nn*no_cycles/len(nn))
        ci = np.cos(2*np.pi*nn*no_cycles/len(nn))
        return ci + 1j*si

    def plotCS(sig, centre=0, span=100):
        """plot a slice of sig"""
        xx = range(centre-span//2, centre+span//2)
        return (xx, np.take(sig.real, xx), xx, np.take(sig.imag, xx))

    def querySampling(dev):
        adc1 = dev.adc.channels[0]
        adc2 = dev.adc.channels[1]
        dac1 = dev.dac.find_channel('voltage0', True)
        dac2 = dev.dac.find_channel('voltage1', True)
        print(' adc1: {:5.2f}MHz available:[{:5.2f}, {:4.2f}]'.\
              format(_sampling(adc1), *_available(adc1)))
        print(' adc2: {:5.2f}MHz available:[{:5.2f}, {:4.2f}]'.\
              format(_sampling(adc2), *_available(adc1)))
        print(' dac1: {:5.2f}MHz available:[{:5.2f}, {:4.2f}]'.\
              format(_sampling(dac1), *_available(adc1)))
        print(' dac2: {:5.2f}MHz available:[{:5.2f}, {:4.2f}]'.\
              format(_sampling(dac2), *_available(adc1)))
