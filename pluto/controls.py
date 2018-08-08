"""
    Constants for contol of pluto sdr and dds 
                                                     rgr01aug18
"""

# for setting the state of devices
ON = True
OFF = False

# for data conversion
import numpy
FLOAT = numpy.float64       # keep 2:1 proportion so that np.view() performs
COMPLEX = numpy.complex128  # a fast in place conversion of interleaved IQ

def devFind(ctx, name):
    dev = ctx.find_device(name)
    if dev is None:
        raise NameError('device '+name+' not found')
    return dev

