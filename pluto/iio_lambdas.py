"""
    Functions to read and write values tovarious iio Attribute classes
    They all use strings to represent numbers, some with value scaling 
    and some with units appended to the end.
                                                            rgrjul2518
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

# frequencies are in MHz, but the value set is a str in Hz
_M2Str = lambda x: str(int(x*1e6))          # convert MHz float to string in Hz
_Str2M = lambda x: float(x)/1e6             # and back
# phase is set in degrees to 3 decimal places but stored as a str in degs*1000
_P2Str = lambda x: str(int(round(x,3)*1e3)) # convert degs float*1000 to string
_Str2P = lambda x :float(x)/1e3             # and back  
# phase is normalised to 0 <= x <= 360
_PNorm = lambda x: _PNorm(x+360) if x<0 else _PNorm(x-360) if x>360 else x
# amplitude value
_Str2A = lambda x :float(x)                 # convert string amplitude to float

