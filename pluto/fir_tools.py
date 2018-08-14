"""
   Basic FIR designs and plotting

                                                          rgr14Aug18
"""
from __future__ import print_function

from scipy import signal as sig

PASS_TYPES = ('LPF', 'HPF', 'BPF')
PLOT_COLOURS = ('b', 'r')

def lpf(n, cutoff, window='hamming'):
    return sig.firwin(n, cutoff, window=window)
    
def hpf(n, cutoff, window='hanning'):
    return sig.firwin(n, cutoff, window=window, pass_zero=False)

def bpf(n, lower_cutoff, upper_cutoff, window='blackmanharris'):
    a1 = lpf(n, lower_cutoff, window)
    a2 = hpf(n, upper_cutoff, window)
    # combine to for BPF
    return -(a1 + a2)


def fir_taps(pass_type, n, cutoff, window):
    if not pass_types.upper() in PASS_TYPES:
        print('unknown: filter type ' + pass_type)
        return
    pass

from matplotlib import pyplot as plt
import numpy as np

def fir_plot(b, a=1, grid=True, phase=False):
    """plot magnitude in dB and optionally phase together"""
    w, h = sig.freqz(b, a)
    w_norm = w/max(w)
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    plt.plot(w_norm, 20*np.log10(np.abs(h)), PLOT_COLOURS[0])
    plt.title('FIR Frequency Response')
    plt.xlabel('Normalised Frequency [rads/sample]')
    plt.ylabel('Amplidude [dB]', color=PLOT_COLOURS[0])
    if phase:
        ax2 = ax1.twinx()
        rads = np.unwrap(np.angle(h))
        plt.plot(w_norm, rads, PLOT_COLOURS[1])
        plt.ylabel('Phase [rads/sample]', color=PLOT_COLOURS[1])
    if grid:
        plt.grid()
    #plt.axis('tight')
    plt.show()
               
