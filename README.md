


PlutoSDR
========

A package for access and control the PlutSDR hardware.  The PlutoSdr file defines a class for control of 
the hardware.  There is a 2 tone DDS generator built into the Tx firmware and a separate file and
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

The example above uses the default url for creating the PlutoSdr class instance.  The instance has properties to control RF functions of both the Rx and the Tx as well as the internal DDS to transmit up to 2 tones for testing.  In general, frequency controls are in MHz and amplitude controls are dBfs.  There are also functions to readRx() and writeTx() samples, providing a straight forward interface to the RF hardware.  Data can be transferred via numpy arrays either as interleaved IQ np.int16 or complex floats via np.complex128.

Testing
-------
Basic unittests are included, but are limited to confirming the operation of properies and simple functions.

python -m unittest discover

Tests using the hardware such as transmitting and receiving data can be tried using the ipython notebooks included.
* iio_context_test.ipynb
  * Demonstrating access to the internal devices using the iio module
 * pluto_test.ipynb
   * Demonstrating readRx and writeTx functions

License
-------
This software is Copyright (C) 2018 Radio System Design Ltd. and released under GNU Lesser General Public License.  See the license file in the repository for details.