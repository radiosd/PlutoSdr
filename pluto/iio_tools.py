"""
   Tools to access iio structures and internal attributes
   Context is the top level with attributes and a list of devices
   Devices have attributes and a list of channels
   Channels are input or output to transfer data with control attibutes

                                                          rgr15jul18
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

import iio

def iioFind(iio_item, name):
    """locate and return the named item from that given"""
    if iio_item is None:
        raise NameError('device '+name+' not found')
    if isinstance(iio_item, iio.Context):
        found = iio_item.find_device(name)
    if isinstance(iio_item, iio.Device):
        found = iio_item.find_channel(name)
    return found


def iioList(item):
    """show information on the iio_class instance given"""
    # info is appropriate for the class supplied
    if isinstance(item, iio.Context):
        print(listContext(item))
    elif isinstance(item, iio.Device):
        print(listDevice(item))
    elif isinstance(item, iio.Channel):
        print(listChannel(item))
    elif isinstance(item, list):
        for each in item:
            iioList(each)
    elif isinstance(item, dict):   # all the various Attr classes
        for k, v in item.items():
            if isinstance(v, str):
                value = v
            else:
                value = _showAttr(v)
            print(k, ':', value)
    else:
        print('unknown item:')
        for k, v in item.items():
            print(k, v.value, ',', end='')

def _showAttr(attr):
    try:
        v = attr.value
    except Exception as e:
        v = type(e) # + ' '.join(e.args)
    return v

def _getAttrs(item):
    try:
        ats = len(item.attrs)
    except AttributeError:
        ats = 0
    return ats

def _getDebugAttrs(item):
    try:
        d_ats = len(item.debug_attrs)
    except AttributeError:
        d_ats = 0
    return d_ats

def listContext(item):
    """return summary of context properties"""
    attrs = _getAttrs(item)
    debug_attrs = _getDebugAttrs(item)
    return 'name:{:s}, attrs({:d}), devices({:d}), debug_attrs({:d})'\
           .format(item.name, attrs, len(item.devices), debug_attrs)

def listDevice(dev):
    """return summary of device properties"""
    name = '_' if dev.name is None else dev.name
    idx = '_' if dev.id is None else dev.id
    try:
        ats = len(dev.attrs)
    except AttributeError:
        ats = 0
    chs = len(dev.channels)
    try:
        d_ats = len(dev.debug_attrs)
    except AttributeError:
        d_ats = 0
    return '{:s}, name:{:s}, attrs({:d}), channels({:d}), debug_attrs({:d})'\
           .format(idx, name, ats, chs, d_ats)

def listChannel(item):
    """return summary of channel properties"""
    attrs = _getAttrs(item)
    idx = '_' if item.id is None else item.id
    name = '_' if item.name is None else item.name
    io = 'output' if item.output else 'input'
    return 'id:{:s} name:{:s}, attrs({:d}), {:s}'\
           .format(idx, name, attrs, io)
    
if __name__=='__main__':
    from pluto_sdr import PlutoSdr
    pp = PlutoSdr()
    iioList(pp.ctx)   # a context
    iioList(pp.dds)   # a device
    iioList(pp.ctx.devices)  # device list
    iioList(pp.dds.channels[0])  # a channel
    cc0 = pp.dds.channels[0]
    catt = cc0.attrs['phase']    # ChannelAttr
    iioList(pp.dds.channels)     # a channel list

    dd1 = pp.ctx.devices[1]
    datt = dd1.attrs['calib_mode_available']  # device DebugAttr
    ddatt = dd1.debug_attrs['digital_tune']
    cc = pp.dds.channels

    #iioList(dd1.attrs)
    #iioList(dd1.debug_attrs)
