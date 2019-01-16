PlutoSDR
========

A package for access and control the PlutSDR hardware.  The PlutoSdr file defines a class for control of 
the hardware.  There is a 2 tone DDS generator built into the Tx firmware and there is a separate file and
class used to define the control of that.  An instance of PlutoSdr automatically creates the DDS 

Getting Started
---------------
Dependancies:

iio 
 - clone from https://github.com/analogdevicesinc/libiio.git and 
 - follow standard cmake, built etc
 - the iio library is installed using setup.py in bindings/python

changeExt
 - clone from https://github.com/radiosd/rsdLib.git
 - use setup.py to install

Installation
------------
Installation of PlutoSdr is via the standard python setup.py install. Then:

```python
from pluto.pluto_sdr import PlutoSdr

sdr = PlutoSdr()
```

The example above uses the default url for creating the PlutoSdr class instance.  The instance has properties to control RF functions of both the Rx and the Tx as well as the internal DDS to transmit up to 2 tones for testing.  In general, frequency controls are in MHz and amplitude controls are dBfs.  There are also functions to readRx() and writeTx() samples, providing a straight forward bytearray interface to the RF hardware.

License
-------
This software is Copyright (C) 2018 Radio System Design Ltd. and released under GNU Lesser General Public License.  See the license file in the repository for details.
