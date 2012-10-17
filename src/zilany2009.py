#!/usr/bin/env python

"""Zilany, M. S. A., Bruce, I. C., Nelson, P. C., and Carney,
L. H. (2009). A phenomenological model of the synapse between the
inner hair cell and auditory nerve: long-term adaptation with
power-law dynamics. The Journal of the Acoustical Society of America,
126(5):2390-2412.

"""

from __future__ import division
from __future__ import print_function

__author__ = "Marek Rudnicki"

import warnings
import itertools

import numpy as np
import pandas as pd

from . import _pycat



def run_zilany2009(
        sound,
        fs,
        anf_num,
        seed,
        cf,
        cohc=1,
        cihc=1,
        powerlaw_implnt='approx'):



    np.random.seed(seed)

    assert np.max(sound) < 1000, "Signal should be given in Pa"
    assert sound.ndim == 1




    cfs = _calc_cfs(cf)





    ### Run Middle Ear filter
    meout = _pycat.run_me(signal=sound, fs=fs)


    channel_args = [
        {
            'sound': sound,
            'cf': freq,
            'fs': fs,
            'cohc': cohc,
            'cihc': cihc,
            'anf_num': anf_num,
            'powerlaw_implnt': powerlaw_implnt,
        }
        for freq in cfs
    ]




    if parallel:
        import multiprocessing

        pool = multiprocessing.Pool()
        nested = pool.map(_run_channel, channel_args)

    else:
        nested = map(_run_channel, channel_args)

    trains = itertools.chain(nested)
    spike_trains = pd.DataFrame(
        trains
    )

    np.fft.fftpack._fft_cache = {}

    return spike_trains




def _run_channel(args):

    vihc = _pycat.run_ihc(
        signal=args['signal'],
        cf=args['cf'],
        fs=args['fs'],
        cohc=float(args['cohc']),
        cihc=float(args['cihc'])
    )

    duration = len(vihc) / fs
    anf_types = np.repeat(['hsr', 'msr', 'lsr'], args['anf_num'])
    synout = {'hsr':None, 'msr':None, 'lsr':None}

    trains = []
    for anf_type in anf_types:

        if synout[anf_type] is None:
            synout[anf_type] = _pycat.run_synapse(
                fs=args['fs'],
                vihc=vihc,
                cf=args['cf'],
                anf_type=anf_type,
                powerlaw_implnt=powerlaw_implnt,
                with_ffGn=False
            )

        spikes = _pycat.run_spike_generator(
            fs=fs,
            synout=synout
        )

        spikes = np.array(spikes[spikes != 0])

        trains.append({
            'spikes': spikes,
            'duration': duration,
            'cf': args['cf'],
            'type': anf_type
        })


    return trains





def _calc_cfs(cf):

    if np.isscalar(cf):
        cfs = [float(cf)]

    elif isinstance(cf, tuple):
        # Based on GenerateGreenwood_CFList() from DSAM
        # Liberman (1982)
        aA = 456
        k = 0.8
        a = 2.1

        freq_min, freq_max, freq_num = cf

        xmin = np.log10( freq_min / aA + k) / a
        xmax = np.log10( freq_max / aA + k) / a

        x_map = np.linspace(xmin, xmax, freq_num)
        cfs = aA * ( 10**( a*x_map ) - k)

    elif isinstance(cf, list) or isinstance(cf, np.ndarray):
        cfs = cf

    else:
        raise RuntimeError("CF must be a scalar, a tuple or a list.")

    return cfs



class Zilany2009(object):
    name = 'Zilany2009'

    def __init__(self,
                 anf_num=(1,1,1),
                 cf=1000,
                 cohc=1.,
                 cihc=1.,
                 powerlaw_implnt='approx',
                 with_ffGn=False):
        """ Auditory periphery model of a cat (Zilany et al. 2009)

        anf_num: (hsr_num, msr_num, lsr_num)
        cf: CF
        powerlaw_implnt: 'approx' or 'actual' implementation of the power-law
        with_ffGn: enable/disable Gausian noise

        """
        warnings.warn("Obsolited: use run_zilany2009() instead")


        self._anf_num = anf_num
        self._cf = cf
        self._powerlaw_implnt = powerlaw_implnt
        self._with_ffGn = with_ffGn
        self._cohc = cohc
        self._cihc = cihc


    def run(self, sound, fs, seed):
        """ Run the model.

        fs: sampling frequency of the signal; model is run at the same frequency
        sound: input signal

        """

        trains = run_zilany2009(
            sound=sound,
            fs=fs,
            anf_num=self._anf_num,
            seed=seed,
            cf=self._cf,
            cohc=self._cohc,
            cihc=self._cihc,
            powerlaw_implnt=self._powerlaw_implnt,
            with_ffGn=self._with_ffGn
        )

        return trains
