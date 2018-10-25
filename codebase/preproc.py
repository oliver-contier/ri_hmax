#!/usr/bin/env python


import numpy as np


def add_yborder(img,
                matchbg=True):
    # get img dimensions
    height, width = np.shape(img)
    # amount of padding
    padd = int((width - height) / 2)
    # make square canvas
    canvas = np.zeros((height + padd * 2, height + padd * 2))

    if matchbg:
        # find lower and upper mean pixel values in image
        # and fill in these values at respective border
        lower_pval = np.mean(img[0,:])
        upper_pval = np.mean(img[-1,:])
        canvas[0:padd,:] = lower_pval
        canvas[-padd:-1,:] = upper_pval

    # add image to center of canvas
    canvas[padd:-padd, :] = img
    return canvas
