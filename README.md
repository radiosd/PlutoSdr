PlutoSDR
========

A package for access and control the PlutSDR hardware.  The PlutoSdr file defines a class for control of 
the hardware.  There is a 2 tone DDS generator built into the Tx firmware and there is a separate file and
class used to define the control of that.  An instance of PlutoSdr automatically creates the DDS 

Getting Started
---------------
Dependancies: iio 

Installation is via the standard python setup.py install.

from pluto import PlutoSdr

device = PlutoSdr.PlutoSdr()   

Uses the default url which should be the case for a single device 
The instance has properties to control RF functions of both the Rx and the Tx as well as the internal DDS to transmit up to 2 tones for testing. 
In general frequency controls are in MHz and amplitude controls are dBfs