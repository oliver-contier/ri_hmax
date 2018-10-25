#!/usr/bin/env python

import os
from os.path import abspath as abp
from os.path import join as pjoin

import pandas as pd
import skimage.io as sio
import skimage.transform as sit
from skimage.exposure import equalize_adapthist

from condor_handler import write_submission_file, exec_submission
from preproc import add_yborder


def getfiles_aloi_selection(csv_file='/home/contier/ri_hmax/aloi_selection.csv',
                            db='ALOI (2005)',
                            aloi_db_path=pjoin('/home/data/exppsy/object_databases/Datenbanken',
                                               'ALOI_2005', 'png2'),
                            rot_stepsize=9):
    """
    Get a list of image file names representing 8 viewpoints of each stimulus I chose from the ALOI data base
    and specified in a csv file.

    Parameters
    ----------
    csv_file : str
        path to csv file containing my selection of ALOi stimuli
    db : str
        For now, only ALOI 2005 works
    aloi_db_path : str
        Path to base directory of the ALOI data base.
    rot_stepsize : int
        Step size for choosing every nth viewpoint from the list of available viewpoints.

    Returns
    -------
    filepaths : list
        list of absolute paths for all images.
    """
    db_df = pd.read_csv(csv_file)
    aloi_df = db_df[db_df['database'] == db]
    # get list of file names representing different rotations for each selected stimulus
    filelist = [
        pjoin(aloi_db_path, str(db_num), '%s_r%i.png') % (db_num, rotation)
        # there is _r0 to _r355 in steps of 5, yielding  72 images per object. If we take every 9th file, I get 8.
        for rotation in range(0, 360, 5 * rot_stepsize)
        for db_num in aloi_df['db-number']
    ]
    # surround paths with single quotes to avoid white space confusion
    filepaths = [fpath.replace('.0', '') for fpath in filelist]

    return filepaths


# TODO: Function to run python-hmax on my ALOi selection


def aloi_preproc(imgfile,
                 outfile,
                 downsample=(104, 104),
                 enhance=False,
                 contrast_clip=0.015,
                 lower_thresh=None):
    # add borders to make a square image
    img = sio.imread(imgfile, as_grey=True)
    img_square = add_yborder(img)
    # downsample
    img_down = sit.resize(img_square, downsample)
    if enhance:
        # adaptive histogram equalization for contrast enhancement
        img_down = equalize_adapthist(img_down, clip_limit=contrast_clip)
    if lower_thresh:
        # cut low values
        img_down[img_down < lower_thresh] = 0
    # save image
    sio.imsave(outfile, img_down)
    return outfile


def aloi_selection2percepts(inflist,
                            runscr,
                            baseworkdir='/home/contier/ri_hmax/workdir/aloi/',
                            clean=False):

    # create working directories
    for directory in [baseworkdir,
                      pjoin(baseworkdir, 'preprocessed'),
                      pjoin(baseworkdir, 'percepts')]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # create preprocessing output file names
    prep_outflist = [pjoin(baseworkdir, 'preprocessed',
                           inf.split('/')[-1].replace('.png', '_prep.png'))
                     for inf in inflist]

    # create ri simulation output filenames
    outflist = [pjoin(baseworkdir, 'percepts',
                      inf.split('/')[-1].replace('.png', '_ri_percept.png'))
                for inf in inflist]

    # creat and run submission file
    submitf = write_submission_file(runscript=runscr, arglist1=inflist,
                                    arglist2=prep_outflist, arglist3=outflist)
    exec_submission(submit_fpath=abp(submitf), cleanup=clean)
    print('Submitted ALOI selection to condor for simulation with script %s' % runscr)

    return outflist
