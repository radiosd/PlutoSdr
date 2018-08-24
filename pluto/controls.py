"""
    Constants for contol of pluto sdr and dds 
                                                          rgr01aug18
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

# for setting the state of devices
ON = True
OFF = False

# for data conversion
import numpy
FLOAT = numpy.float64       # keep 2:1 proportion so that np.view() performs
COMPLEX = numpy.complex128  # a fast in place conversion of interleaved IQ

def devFind(ctx, name):
    """find an iio_device by name or raise and exception"""
    dev = ctx.find_device(name)
    if dev is None:
        raise NameError('device '+name+' not found')
    return dev

