#!/usr/bin/env python


"""
Crop percept images from Lihuis experiment and take the first frame to remove time dimension
"""


import skimage.io as sio
from skimage.transform import resize as skresize
import glob
import os
import numpy as np


def crop_im(im_fname, out_fname, downsample=True):
    """
    Load image, remove white margin, and save to file.
    Use .png extension to avoid compression.
    """
    im = sio.imread(im_fname)
    im_first = im[:,:,0]  # first frame
    wval = im_first[0,0]  # value of top left pixel (should be white)
    # mask and coordinates of non-white pixel
    immask = im_first != wval
    imcoords = np.argwhere(immask)
    # creat bounding box to crop
    x0, y0 = imcoords.min(axis=0)
    x1, y1 = imcoords.max(axis=0) + 1  # slices are exclusive at the top
    # crop and save
    cropped = im_first[x0:x1, y0:y1]

    if downsample:
        cropped = skresize(cropped, (104, 104))

    sio.imsave(out_fname, cropped)

print('glob files')

# List of Lihui's files (absolute paths)
flist = [os.path.abspath(filename) for filename in glob.glob('./sim_lihui/*.png')]
# Equivalent list of filenames for output
outlist = [filename.replace('sim_lihui', 'sim') for filename in flist]

# create directory
if not os.path.exists('./sim'):
    os.makedirs('./sim')

print('start loop')

# Loop through input and output names
for inf, outf in zip(flist, outlist):
    crop_im(inf, outf)
