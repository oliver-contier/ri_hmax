#!/usr/bin/env/python

"""
Notes
-----
AlphaIMS configuration: e_spacing = 72, e_radius = 50, ncols and nrows=37

"""

import numpy as np
import skimage.io as sio
import skimage.transform as sit
from supersim.static import Simulator


def supersim_img(imgfile,
                 downsample=(104, 104)):
    """
    Use Johannes supersim to transform an image into an ri percept.

    Parameters
    ----------
    imgfile : str
        path to input image file
    downsample : bool, tuple, optional
        if not False, downsample the input image to the specified resolution

    Returns
    -------
    percept_max : array
        brightest frame of the produced RI percept.
    """
    # load and downsample input file
    img_in = sio.imread(imgfile, as_gray=True)
    if downsample:
        img_in = sit.resize(img_in, downsample)
    # initialize simulation
    simulator = Simulator(max_spread=0, use_gpu=0, placement='subretinal',
                          n_rows=37, n_cols=37, impl_center_x=0, impl_center_y=0,
                          e_distance=72, e_size=50,
                          s_sampling=25, t_sample=0.4 / 1000)
    simulator.initialize_stimulus(stim_duration=200)
    simulator.image_to_pulse_train(imgfile, amp_range=[0, 20])
    # run simulation
    percept = simulator.simulate_percept()
    # extract brightest frame
    percept_max = percept[:, :, np.unravel_index(percept.argmax(), percept.shape)[-1]]
    return percept_max


if __name__=='__main__':
    #  make this also suitable as runscript for use with condor
    import sys
    infile = sys.argv[1]
    outfile = sys.argv[2]

    percept = supersim_img(infile)
    sio.imsave(outfile, percept)