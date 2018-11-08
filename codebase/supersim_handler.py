#!/usr/bin/env/python

"""
Notes
-----
"""

import numpy as np
import skimage.io as sio
import skimage.transform as sit
from skimage import img_as_float, img_as_ubyte
from supersim.static import Simulator

from aloi_handler import aloi_preproc


def supersim_img(imgfile,
                 downsample=None):
    """
    Use Johannes supersim to transform an image into an ri percept.

    Parameters
    ----------
    imgfile : str
        path to input image file
    downsample : tuple, optional
        if specified, downsample the input image to the specified resolution

    Returns
    -------
    percept_max : array
        brightest frame of the produced RI percept.
    """
    # load and downsample input file
    img_in = sio.imread(imgfile, as_gray=True)
    img_in = img_as_float(img_in)
    # only grab one of the image "depth" dimensions
    if len(np.shape(img_in)) == 3:
        img_in = img_in[:, :, 0]
    if downsample:
        img_in = sit.resize(img_in, downsample)

    # initialize simulation
    # AlphaIMS configuration: e_spacing = 72, e_radius = 50, ncols and nrows = 37
    # max_spread is set to 500 microns by default
    # (determines the size of simulated retina beyond the implant, impacts output size)
    simulator = Simulator(use_gpu=0, placement='subretinal',
                          n_rows=37, n_cols=37, impl_center_x=0, impl_center_y=0,
                          e_distance=72, e_size=50,
                          s_sampling=25, t_sample=0.4 / 1000)
    simulator.initialize_stimulus(stim_duration=200)
    simulator.image_to_pulse_train(img_in, amp_range=[0, 20])
    # run simulation
    percept = simulator.simulate_percept()
    # extract brightest frame
    percept_max = percept[:, :, np.unravel_index(percept.argmax(), percept.shape)[-1]]
    return percept_max


if __name__ == '__main__':
    """
    This part acts as the pipeline for RI simulation of a single image
    to run via the supersim_runscript.sh on condor
    """
    import sys

    infile = sys.argv[1]
    preppedfile = sys.argv[2]
    outfile = sys.argv[3]

    preppedfile = aloi_preproc(infile, preppedfile)
    percept = supersim_img(preppedfile)

    # convert to uint8 format bc else psychopy won't display properly
    percept_uint8 = img_as_ubyte(percept)

    sio.imsave(outfile, percept_uint8)
