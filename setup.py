#!usr/bin/env python
"""
    setup for code to access and control the PlutSDR hardware
    
                                                        rgr05Aug18
"""

from distutils.core import setup

VERSION_FILE = 'pluto/version.py'
# read version and other information from the package
version = {}
with open(VERSION_FILE) as fin:
    exec(fin.read(), version)

setup(name='PlutoSDR',
      version = version['__version__'],
      description = \
         'The library package for access and control the PlutSDR hardware',
      author = 'Richard Ranson',
      scripts = [],   # add name(s) of script(s)
      packages = [pluto]   # add name(s) of package(s)
      )

# I'm sure there is more to add, but for now ok to install packaged and scripts
