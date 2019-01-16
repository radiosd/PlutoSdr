"""
   Access to and control of pluto fir filters
                                                          rgr11Aug18
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
from __future__ import print_function
from rsdLib.fileUtils import changeExt

# SPI control register locations
TX_COEFF_ADDR = 0x60     # read/write from/to this coeff offset
TX_WRITE_REG  = 0x61     # this is lsb, with usb at 0x62
TX_READ_REG   = 0x63     # this is lsb, with usb at 0x64
TX_FIR_CONFIG = 0x65     # see txConfig()

RX_COEFF_ADDR = 0xF0     # read/write from/to this coeff offset
RX_WRITE_REG  = 0xF1     # this is lsb, with usb at 0xF2
RX_READ_REG   = 0xF3     # this is lsb, with usb at 0xF4
RX_FIR_CONFIG = 0xF5     # see rxConfig()
RX_FIR_GAIN   = 0xF6     # <1:0> filter gain

# registers hold 16 bit 2s compliment values in consecutive LSB, MSB addresses
# helper functions hard coded for two 8 bit bytes
import numpy as np

def twosC2Int(b1, b0):
    """integer from 2 byte twos compliment representation"""
##    v = ((b1<<8) + b0 )
##    return v -(1<<16) if b1 & (1<<7) else v
    return np.int16((b1<<8) + b0)

def int2TwosC(value):
    """2 byte twos compliment representation of value given"""
##    b1, b0 = divmod(value, 1<<8)
##    if b1<0 :
##        b1 += 1<<8
    b1, b0 = divmod(np.int16(value), 1<<8)
    return (np.ubyte(b1), np.ubyte(b0))

def setBit(index, value, on):
    mask = 1<<index
    value &= ~mask            # clear the bit
    if on:
        value |= mask         # set the bit
    return value

import logging
import os
from pluto.controls import ON, OFF

class FirConfig(object):
    def __init__(self, device):
        self.ftr_file = None
        self.dev = device
        self.ch = device.find_channel('out')
    # -------------------- on/off filter control -----------------------
    def enable(self):
        self.ch.attrs['voltage_filter_fir_en'].value = '1'

    def disable(self):
        self.ch.attrs['voltage_filter_fir_en'].value = '0'
    # -------------------- configuration control -----------------------
    def configReg(self, trx):
        """return config control reg for Tx or Rx"""
        if trx.upper()[0]=='T':
            return TX_FIR_CONFIG
        elif trx.upper()[0]=='R':
            return RX_FIR_CONFIG
        else:
            raise ValueError('unknown signal path must be tx or rx')

    def clock(self, trx, on):
        """clock control is <1> in  T or R config register"""
        c_reg = self.configReg(trx)
        value = self.dev.reg_read(c_reg)
        self.dev.reg_write(c_reg, setBit(1, value, on))

    def write(self, trx, on):
        """write control is <2> in  T or R config register"""
        c_reg = self.configReg(trx)
        value = self.dev.reg_read(c_reg)
        self.dev.reg_write(c_reg, setBit(2, value, on))

    def txConfig(self, no_taps, gain):
        """pluto has only 1 tx channel"""
        if no_taps>128 and not (no_taps % 16==0):
            raise ValueError('invalid number of taps')
        # format data for the register
        b7_5 = ((no_taps//16) - 1)<<5    # <7:5> number of taps
        b4_3 = 3<<3                      # <4:3> select TX 1, 2 or 3=both
        b2 = 0                           # <2>   write
        b1 = 0                           # <1>   Start clock
        b0 = 0 if gain==0 else 1         # <0>   filter gain set = -6dB
        value = b7_5 + b4_3 + b2 + b1 + b0
        logging.info('Tx config 0x{:x}'.format(value))
        self.dev.reg_write(TX_FIR_CONFIG, value)

    def rxConfig(self, no_taps, gain):
        """pluto has only 1 rx channel"""
        if no_taps>128 and not (no_taps % 16==0):
            raise ValueError('invalid number of taps')
        # format data for the register
        b7_5 = ((no_taps//16) - 1)<<5    # <7:5> number of taps
        b4_3 = 3<<3                      # <4:3> select RX 1, 2 or 3=both
        b2 = 0                           # <2>   write
        b1 = 0                           # <1>   Start clock
        b0 = 0                           # reserved
        value = b7_5 + b4_3 + b2 + b1 + b0
        logging.info('Rx config 0x{:x}'.format(value))
        self.dev.reg_write(RX_FIR_CONFIG, value)
        # rx gain settings are +6, 0, -6, -12dB
        gain = (gain+6)//6
        # <1:0>   filter gain   +6, 0, -6, -12dB
        logging.info('Rx gain 0x{:x}'.format(gain))
        self.dev.reg_write(RX_FIR_GAIN, gain)
    # ------------------------ write to fir ----------------------------
    def pushCoeffs(self, trx):
        """trigger write of values to T or R fir registers"""
        self.dev.reg_write(self.configReg(trx), 0xFE)

    def writeRegPair(self, addr, value):
        b1, b0 = int2TwosC(value)
        self.dev.reg_write(addr, b0)
        self.dev.reg_write(addr+1, b1)

    def writeTx(self, coeffs):
        """write coeff vector to the TX fir"""
        self.disable()
        self.clock('tx', ON)
        self.write('tx', ON)
        # loop through all writing the values from offset 0
        for i in range(len(coeffs)):
            self.dev.reg_write(TX_COEFF_ADDR, i)
            self.writeRegPair(TX_WRITE_REG, coeffs[i])
            self.pushCoeffs('tx')
        for i in range(len(coeffs), 128):   # zero any remaining
            self.dev.reg_write(TX_COEFF_ADDR, i)
            self.writeRegPair(TX_WRITE_REG, 0)
            self.pushCoeffs('tx')
        # disable writing
        self.clock('tx', OFF)
        self.write('tx', OFF)
        self.enable()

    def writeRx(self, coeffs):
        """write coeff vector to the RX fir"""
        self.disable()
        self.clock('rx', ON)
        self.write('rx', ON)
        # loop through all writing the values from offset 0
        for i in range(len(coeffs)):
            self.dev.reg_write(RX_COEFF_ADDR, i)
            self.writeRegPair(RX_WRITE_REG, coeffs[i])
            self.pushCoeffs('rx')
        for i in range(len(coeffs), 128):   # zero any remaining
            self.dev.reg_write(RX_COEFF_ADDR, i)
            self.writeRegPair(RX_WRITE_REG, 0)
            self.pushCoeffs('rx')
        # disable writing
        self.clock('rx', OFF)
        self.write('rx', OFF)
        self.enable()
    # ------------------------ read from fir ---------------------------
    def readRegPair(self, start_add):
        """read consecutive registers, LSB, MSB"""
        lsb = self.dev.reg_read(start_add)
        usb = self.dev.reg_read(start_add+1)
        return twosC2Int(usb, lsb)

    def readTx(self):
        """read and return all the TX FIR coeffs"""
        self.dev.reg_write(TX_FIR_CONFIG, 0xEA)
        coeffs = []
        for addr in range(0x80):
            self.dev.reg_write(TX_COEFF_ADDR, addr)
            coeffs.append(self.readRegPair(TX_READ_REG))
        return np.trim_zeros(coeffs) # remove leading/trailing zeros

    def readRx(self):
        """read and return all the RX FIR coeffs"""
        self.dev.reg_write(RX_FIR_CONFIG, 0xEA)
        coeffs = []
        for addr in range(0x80):
            self.dev.reg_write(RX_COEFF_ADDR, addr)
            coeffs.append(self.readRegPair(RX_READ_REG))
        return np.trim_zeros(coeffs) # remove leading/trailing zeros
    # ------------------- read Tx and Rx firs from file-----------------
    def loadFile(self, filename):
        """read filter and config data from a ftr file"""
        self.disable()
        filename = changeExt(filename, 'ftr')
        if os.path.isfile(filename):
            with open(filename, 'r') as fin:
                ftr_file = fin.read()
            self.dev.attrs['filter_fir_config'].value = ftr_file
        else:
            raise FileNotFoundError(filename+' not found')
        self.enable()

if __name__=='__main__':
    import sys
    import iio
    logging.basicConfig(
        format='%(module)-12s.%(funcName)-12s:%(levelname)s - %(message)s',
        stream=sys.stdout, level=logging.DEBUG)
    try:  # iio returns None if items are not found
        ctx = iio.Context('ip:pluto.local')
        if ctx is not None:
            dev = ctx.find_device('ad9361-phy')
        else:
            raise IOError('iio context not found')
        fir = FirConfig(dev)

        #fir.loadFile('test/GSM.ftr')
    except IOError as er1:
        print('requires an ADALM Pluto to be connected')
