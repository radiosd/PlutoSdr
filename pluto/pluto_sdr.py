"""
    Basic class to simplifiy interaction with pluto as an iio device
                                                            rgr12jan18
 * Copyright (C) 2018 Radio System Design Ltd.
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
from pluto.controls import ON, OFF, FLOAT, COMPLEX

class PlutoSdr(object):
    """Encapsulation of Pluto SDR device
       iio lib interface used to expose common functionality
       RF signal data read/write capabilities for rx and tx"""
    no_bits = NO_BITS
    TX_OFF = 0
    TX_DMA = 1
    TX_DDS = 2
    def __init__(self, uri=PLUTO_ID):
        # access to internal devices
        try:
            self.ctx = iio.Context(uri)
        except OSError:
            self.ctx = None
            print('exception: no iio device context found at',uri)
            return
        logging.debug('found context for pluto device')
        self.name = 'plutosdr'
        self.phy = self.ctx.find_device('ad9361-phy')
        # individual TRx controls
        self.phy_rx = self.phy.find_channel('voltage0', is_output=False)
        self.phy_tx = self.phy.find_channel('voltage0', is_output=True)
        # access to data channels for Rx
        self.adc = self.ctx.find_device('cf-ad9361-lpc')
        # access to data channels for Tx
        self.dac = self.ctx.find_device('cf-ad9361-dds-core-lpc')
        self.tx_channels = [self.dac.find_channel('voltage0', True)]
        self.tx_channels.append(self.dac.find_channel('voltage1', True))        
        # also access to the internal 2 tone generator
        self.dds = pluto_dds.Dds(self.dac)
        #  tx buffer, created in writeTx and retained for continuous output 
        self._tx_buff = None
        self.tx_state = self.TX_OFF
        
    # ----------------- TRx Physical Layer controls -----------------------
    def _get_SamplingFreq(self):
        """internal sampling frequency in MHz (ADC and DAC are the same)"""
        # available from many channel none of which are named
        # changes to [4] seem to alter them all
        value = self.phy_rx.attrs['sampling_frequency'].value
        return int(value)/1e6

    def _set_SamplingFreq(self, value):
        """set internal sampling freq in MHz"""
        # 2.1<value<30, use interpolation for lower sampling rates
        try:
            self.phy_rx.attrs['sampling_frequency'].value = _M2Str(value)
        except OSError:
            print('value out of range:', value)

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
        
    def loopBack(self, enable):   # not clear how to control the injection to/from option
        """turn loop-back function on/off"""
        _enable = '1' if bool(enable) else '0'
        self.phy.debug_attrs['loopback'].value = _enable

    # ---------------------- Receiver control-------------------------
    # property actual value may be slightly different because the
    # firmware converts them to available value from the synth
    def rxStatus(self):
        """print the key parameters for the receive signal chain"""
        print('Rx Fs:{:2.1f}MHz\tBB: {:7.2f}MHz'\
              .format(self.sampling_frequency, self.rxBBSampling()))
        print('   BW:{:2.1f}MHz\tLO: {:7.2f}MHz'\
              .format(self.rx_bandwidth, self.rx_lo_freq))
        print(' Gain:{:2.1f}dB\tMode: {:s}'\
              .format(self.rx_gain, self.phy_rx.attrs['gain_control_mode'].value))

    def rxBBSampling(self):
        """the rx base band sampling rate in MHz"""
        fs = self.sampling_frequency
        return fs/8 if self.rx_decimation else fs
        
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
            # only 2 options adc_rate or adc_rate/8
            _enable = enable!=0
            _adc = self.adc.channels[0].attrs
            options = _adc['sampling_frequency_available'].value.split(' ')
            _adc['sampling_frequency'].value = options[_enable!=0]
            logging.debug('set: rx_decimation:>' + str(options[_enable]))
        else:
            raise ValueError('bool expected: only 2 options for rx_sampling')
        
    rx_decimation = property(_get_rxDownSampling, _set_rxDownSampling)

    def _get_rxLoFreq(self):
        """get receiver LO frequency property in MHz"""
        value = self.phy.find_channel('RX_LO').attrs['frequency'].value
        return int(value)/1e6

    def _set_rxLoFreq(self, value):
        """set receiver LO frequency property in MHz"""
        self.phy.find_channel('RX_LO').attrs['frequency'].value = _M2Str(value)        
    rx_lo_freq = property(_get_rxLoFreq, _set_rxLoFreq)
    
    def _get_rxBW(self):
        """get receiver analogue RF bandwidth in MHz"""
        value = self.phy_rx.attrs['rf_bandwidth'].value
        return int(value)/1e6

    def _set_rxBW(self, value):
        """set receiver analogue RF bandwidth in MHz"""
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
        """set the gain mode to one of those available"""
        avail = self.phy_rx.attrs['gain_control_mode_available'].value
        avail = avail.split() 
        # allow setting with just the first letter
        _mode = '' if len(mode)==0 else mode[0].upper()                    
        options = [av.capitalize()[0] for av in avail]
        if _mode in options:
            res = avail[options.index(_mode)]
            self.phy_rx.attrs['gain_control_mode'].value = res
            logging.debug('gain mode set:', res)
        else:
            print('error: available modes are', avail)
    
    def _get_rx_gain_mode(self):
        """get the gain mode to one of those available"""
        return self.phy_rx.attrs['gain_control_mode'].value
    rx_gain_mode = property(_get_rx_gain_mode, _set_rx_gain_mode)
    
    def _get_rx_rssi(self):
        """return rx rssi value"""  # this is 'ddd.dd dB'
        return self._phy.channels[5].attrs['rssi'].value
    rsssi = property(_get_rx_rssi, None)  # read only
    
    # getting data from the rx  
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
        ans['fs'] = self.sampling_frequency
        ans['fc'] = self.rx_lo_freq
        ans['rx_bw'] = self.rx_bandwidth
        ans['rx_gain'] = self.rx_gain
        ans['data'] = self.readRx(no_samples, raw=raw)
        # for raw data the device must provide the no of bits
        if raw:                     
            ans['bits'] = self.no_bits   
        return ans              
    # -------------------- Transmitter control------------------------
    # 3 mutually exclusive states off, dma - transmit data using writeTx()
    # or dds - 1 or 2 tone output controlled via dds instance
    def _txDMA(self, value):
        """control DMA channels"""
        for ch in self.tx_channels:
            ch.enabled = value
            
    def _set_tx_state(self, value):
        """states are OFF, DMA (via a buffer) or DDS"""
        self._tx_state = value
        if value==self.TX_DMA:
            self._txDMA(ON)
            self.dds.state(OFF)
        elif value==self.TX_DDS:
            self._txDMA(OFF)
            self.dds.state(ON)
        else:                        # any other value is TX_OFF
            self.dds.state(False)    # this must be first don't know why
            self._txDMA(False)
            self._tx_buff = None
            
    def _get_tx_state(self):
        return ('off', 'dma', 'dds')[self._tx_state]
    tx_state = property(_get_tx_state, _set_tx_state)
        
    def txStatus(self, showDds=False):
        """print the key parameters for the receive signal chain"""
        print('Tx Fs:{:5.1f}MHz\tBB: {:7.2f}MHz'\
              .format(self.sampling_frequency, self.txBBSampling()))
        print('   BW:{:5.1f}MHz\tLO: {:7.2f}MHz'\
              .format(self.tx_bandwidth, self.tx_lo_freq))
        print(' Gain:{:4.1f}dB\tState: {:s}'\
              .format(self.tx_gain, self._get_tx_state()))
        if not(self._tx_buff is None):
            print(' Data:{:d}'.format(len(self._tx_buff)//4))
        if self._tx_state==self.TX_DDS or showDds:
            fmt = ' dds{:n}: {:5.3f}V\t{:5.3f}MHz\t{:5.2f}degs'
            print(fmt.format(1, *(self.dds.t1.status())))
            print(fmt.format(2, *(self.dds.t2.status())))

    def txBBSampling(self):
        """the base band sampling rate in MHz"""
        fs = self.sampling_frequency
        return fs/8 if self.tx_interpolation else fs
    
    def _get_txUpSampling(self):
        """control transmitter output interpolation"""
        # only 2 options dac_rate or dac_rate/8
        _dac = self.tx_channels[0].attrs
        value = _dac['sampling_frequency'].value
        options = _dac['sampling_frequency_available'].value.split(' ')
        logging.debug('get: tx_decimation:<' + value)
        return value==options[1]
            
    def _set_txUpSampling(self, enable):
        if isinstance(enable, bool) or isinstance(enable, int):
            # only 2 options dac_rate or dac_rate/8
            _enable = enable!=0
            _dac = self.tx_channels[0].attrs
            options = _dac['sampling_frequency_available'].value.split(' ')
            _dac['sampling_frequency'].value = options[_enable]
            logging.debug('set: tx_decimation:>' + str(options[_enable]))
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
            raise ValueError('tx gain is an attenuation, so always negative')
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
    
    def writeTx(self, samples):  #, raw=False): use samples.dtype
        """write to the Tx buffer and make it cyclic"""
        if self._tx_buff is not None:
            self._tx_buff = None               # turn off any previous signal
        if not(isinstance(samples, np.ndarray)):          
            logging.debug('tx: off')           # leave with transmitter off
            self.tx_state = self.TX_OFF
            return
        if samples.dtype==np.int16:
            data = samples<<4         # align 12 bit raw to msb
        else:   # samples can come from some DiscreteSignalSource, if so
                # data is complex IQ and scaled to +/-1.0 float range
                # use 16 **not** self.no_bits to align data to msb
            data = self.complex2raw(samples, 16)
        # samples are 2 bytes each with interleaved I/Q value (no_samples = len/4)
        self.tx_state = self.TX_DMA                 # enable the tx channels
        try:  # create a cyclic iio buffer for continuous tx output
            self._tx_buff = iio.Buffer(self.dac, len(data)//4, True)
            count = self._tx_buff.write(data)
            logging.debug(str(count)+' samples transmitted')
            self._tx_buff.push()
        except OSError as oserr:
            self.tx_state = self.TX_OFF
            raise OSError('failed to create an iio buffer') 
        # buffer retained after a successful call
        return count # just for now

    def playback(self, data, level=-10):
        """transmit data captured from a similar device, level in dBFS"""
        if not isinstance(data, dict):
            # logging.error('unexpected data type')
            raise ValueError('dict data type expected')
            return
        self.tx_lo_freq = data['fc']
        self.sampling_rate = data['fs']
        self.tx_gain = level
        samples = data['data']
        raw = not samples.dtype==COMPLEX
        if raw: # samples are interleaved int IQ possibly from another device
            if 'bits' in data.keys():
                re_scale = self.no_bits - data['bits']
                if rescale>0:
                    samples = samples << re_scale
                if rescale<0:
                    samples = samples >> re_scale
        self.tx_state = self.TX_OFF  # may not be needed
        self.tx_state = self.TX_DMA
        self.writeTx(samples)

    def txOutputFreq(self):
        # read only for now - confused as to which one is the controlling value
        # look at the various possibilities
        dac = self.dac.device
        various = {}
        various['TX1_I_F1'] = dac.channels[0].attrs['sampling_frequency'].value
        various['TX1_I_F2'] = dac.channels[1].attrs['sampling_frequency'].value
        various['TX1_Q_F1'] = dac.channels[2].attrs['sampling_frequency'].value
        various['TX1_Q_F2'] = dac.channels[3].attrs['sampling_frequency'].value       

        various['volt0'] = dac.channels[4].attrs['sampling_frequency'].value
        various['volt1'] = dac.channels[5].attrs['sampling_frequency'].value     
        return various
    # ------------------------ DDS Control ---------------------------
##    def ddsState(self, value):                 # now control via tx_state
##        """turn the dds signal(s) on/off"""
##        if value==OFF:
##            self.dds.t1.state(OFF)
##            self.dds.t2.state(OFF)
##        else:
##            self.dds.t1.state(ON)
##            self.dds.t2.state(ON)
        
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

    def queryTx(dev):
        dds_channels = [dev.dac.find_channel('altvoltage0', True)]
        dds_channels.append(dev.dac.find_channel('altvoltage1', True))
        dds_channels.append(dev.dac.find_channel('altvoltage2', True))
        dds_channels.append(dev.dac.find_channel('altvoltage3', True))
        for ch in dev.tx_channels:
            print(ch.name, ch.id, ch.enabled)
        for ch in dds_channels:
            print(ch.name, ch.id, ch.enabled, ch.attrs['raw'].value)

    def txChs(sdr):
        if sdr._tx_buff is None:
            print('DMA:0')
        else:
            print('DMA:', len(sdr._tx_buff)//4)
        print('tx channels')
        for ch in sdr.dds.device.channels: #sdr.tx_channels:
            print(ch.id, 'enabled:',ch.enabled)
        print('dds channels')
        for ch in sdr.dds.device.channels:
            if 'raw' in ch.attrs.keys():
                print(ch.id, ch.name, 'scale:', ch.attrs['scale'].value, 'raw:', ch.attrs['raw'].value)
        
