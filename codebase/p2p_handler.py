#!/usr/bin/env python

"""
Beware that you need to source an env with my modified version of p2p which currently lives under this path on medusa:
'/home/contier/retrep/p2p_mod/p2p_mod_env'
"""

import os
import pulse2percept as p2p
import skimage.io as sio
import skimage.transform as sit
from scipy.misc import imsave
from skimage.util import invert


def _choose_layers(retinamodel='Nanduri2012'):
    """
    Choose the valid layers to work with a given computational model of the retina

    Parameters
    ----------
    retinamodel : str
        model of the retina. must be implemented in the sourced version of p2p

    Returns
    -------
    simlayers : list
        list containing strings pointing to the to be used retina layers.
        can contain the following: ['GCL', 'OFL', 'INL']
    """
    if retinamodel == 'Nanduri2012':
        simlayers = ['GCL', 'OFL']
    elif retinamodel == 'latest' or retinamodel == 'Horsager2009':
        simlayers = ['GCL', 'OFL', 'INL']
    else:
        raise ValueError("The script '%s' could not evaluate the retina-model argument."
                         % str(os.path.basename(__file__)))
    return simlayers


def _import_implant(implant_type='AlphaIMS'):
    """
    Helper function that imports the fitting implant class instance from pulse2percept defined
    by the implant_type string.
    """
    if implant_type == 'AlphaIMS':
        implant = p2p.implants.AlphaIMS
    elif implant_type == 'ArgusI':
        implant = p2p.implants.ArgusI
    elif implant_type == 'ArgusII':
        implant = p2p.implants.ArgusII
    else:
        raise ValueError("Sorry, I don't know this type of implant: %s." % implant_type)
    return implant


def img2percept(infile,
                implant_type='AlphaIMS',
                engine_string='serial',
                s_sample=25,
                t_sample=0.005 / 1000,
                dconst=0.01,
                retinamodel='Nanduri2012',
                naxons=501,
                downsampling_input=None,  # tuple of desired resolution, e.g. (104,104)
                invert_input=False,
                videobool=False,
                tolerance=0.0):
    """
    Run pulse2percept on an input image.

    Parameters
    ----------
    infile : str
        path to input image file
    implant_type : str
        type of implant used for the simulation. Can be from ['AlphaIMS', 'ArgusI', 'ArgusII']
    engine_string : str, default='serial'
        parallelization engine used by p2p
    s_sample
    t_sample
    dconst
    retinamodel
    naxons
    downsampling_input
    invert_input
    videobool
    tolerance

    Returns
    -------

    """
    # TODO: Finish docstring

    # choose implant type
    implant = _import_implant(implant_type)
    # configure simulation
    sim = p2p.Simulation(implant, engine=engine_string, n_jobs=-1, use_jit=False)
    sim.set_optic_fiber_layer(sampling=s_sample, sensitivity_rule='decay', decay_const=dconst, n_axons=naxons)
    sim.set_ganglion_cell_layer(retinamodel, tsample=t_sample)

    # load input image
    if not videobool:
        img_in = sio.imread(infile, as_gray=True)
        if downsampling_input:
            img_in = sit.resize(img_in, (104, 104))
        if invert_input:
            img_in = invert(img_in)

    # generate pulsetrain
    if videobool:
        stim = p2p.stimuli.video2pulsetrain(infile, implant, tsample=t_sample)
    else:
        stim = p2p.stimuli.image2pulsetrain(img_in, implant, tsample=t_sample)

    # choose retina layers to be included in simulation
    simlayers = _choose_layers(retinamodel)
    # generate percept from pulsetrain
    percept = sim.pulse2percept(stim, layers=simlayers, t_percept=t_sample, tol=tolerance)
    return percept


def save_percept(percept,
                 outfile,
                 videobool=False,
                 fps=30):
    """
    Save the percept obtained from a p2p simulation either as video (mp4) or picture (jpg)
    :param percept:
        Result from p2p simulation
    :param videobool:
        Boolean denoting whether a video or picture is asked for.
    :param outfile:
        Absolute path to output file.
    :return:
        Nothing.
    """
    if not videobool:
        frame = p2p.get_brightest_frame(percept)
        imsave(outfile, frame.data)
    else:
        p2p.files.save_video(percept, outfile, fps=fps)
