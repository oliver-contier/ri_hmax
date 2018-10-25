#!/usr/bin/env/python

"""
Notes
-----
AlphaIMS configuration: e_spacing = 72, e_radius = 50, ncols and nrows=37

"""

import numpy as np
from skimage import img_as_float
import skimage.io as sio
import skimage.transform as sit
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
    # TODO: how to set max_spread?
    simulator = Simulator(use_gpu=0, placement='subretinal',  # max_spread=0
                          n_rows=40, n_cols=40, impl_center_x=0, impl_center_y=0,
                          e_distance=70, e_size=50,
                          s_sampling=25, t_sample=0.4 / 1000)
    simulator.initialize_stimulus(stim_duration=200)
    simulator.image_to_pulse_train(img_in, amp_range=[0, 20])
    # run simulation
    percept = simulator.simulate_percept()
    # extract brightest frame
    percept_max = percept[:, :, np.unravel_index(percept.argmax(), percept.shape)[-1]]
    return percept_max


if __name__ == '__main__':
    #  make this also suitable as runscript for use with condor
    import sys

    infile = sys.argv[1]
    preppedfile = sys.argv[2]
    outfile = sys.argv[3]

    preppedfile = aloi_preproc(infile, preppedfile)
    percept = supersim_img(preppedfile)
    sio.imsave(outfile, percept)
