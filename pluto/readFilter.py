"""
    Read the .ftr file from ADI/Matlab and return a dict of contents
                                                          rgr15Aug18
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
from __future__ import print_function

import logging

from os import path
from pluto.iio_lambdas import _Str2M
from rsdLib.fileUtils import changeExt

def _readGain(trx, a_line):
    """channel and gain information"""
    logging.info(a_line)
    params = a_line.split()
    names = params[0::2]
    values = params[1::2]
    names[0] = 'CH'
    return {trx+n:int(v) for n,v in zip(names, values)}

def _readSynth(a_line):
    """synthesiser and internal filer interpolation/decimation"""
    logging.info(a_line)
    if a_line[1:3].upper()=='TX':
        names = ('TXPLL','DAC', 'T2', 'T2', 'TF', 'TXSAMP')
    elif a_line[1:3].upper()=='RX':
        names = ('RXPLL','ADC', 'R2', 'R1,', 'RF', 'RXSAMP')
    else:
        raise IOError('unknown synthesiser setting parameters '+a_line)
    values = a_line.split()[1:]
    return {n:_Str2M(v) for n,v in zip(names, values)}

def _readBwidth(a_line):
    """RF bandwidth for Rx and Tx"""
    logging.info(a_line)
    xx = a_line.split()
    trx = xx[0][2:4].lower()
    return {trx+'_bw':_Str2M(xx[1])}

def readFilter(filename):
    """read an flt file, parsing the lines and collecting data to a dict"""
    filename = changeExt(filename, 'ftr')
    ans = {'file':path.basename(filename)}
    taps = []
    with open(filename, 'r') as fin:
        # read line by line
        line = fin.readline().strip()
        while line:
            logging.debug(str(len(line))+': '+line)
            if len(line)>1 and not(line[0]=='#'):
                #logging.debug('line: '+line)
                # process the line depending on the content
                if line[:2].upper()=='TX':
                    ans.update(_readGain('tx_', line))
                elif line[:2].upper()=='RX':
                    ans.update(_readGain('rx_', line))
                elif line[0].upper()=='R':
                    ans.update(_readSynth(line))
                elif line[0].upper()=='B':
                    ans.update(_readBwidth(line))
                else:   # assume line contains tap values
                    try:
                        taps.append([int(x) for x in line.split(',')])
                    except:
                        raise IOError('invalid tap values '+line)
            # next line
            line = fin.readline().strip()
        # assume only 2 sets of taps in rx, tx order
        # i.e. shape(taps)[1]==2
        # also shape(taps)[0] should be a multiple of 16
        ans['rx_taps'] = [t[0] for t in taps]
        logging.info('rx taps: {:}'.format(len(ans['rx_taps'])))
        ans['tx_taps'] = [t[1] for t in taps]
        logging.info('tx taps: {:}'.format(len(ans['tx_taps'])))     
        return ans

if __name__=='__main__':
    import sys
    logging.basicConfig(format='%(module)-12s.%(funcName)-12s:%(levelname)s - %(message)s',
                        stream=sys.stdout, level=logging.ERROR)
    
