#!/usr/bin/env python

import os
import pickle
from os.path import abspath as abp
from os.path import join as pjoin

import pandas as pd
import skimage.io as sio
import skimage.transform as sit
from skimage import img_as_ubyte
from skimage.exposure import equalize_adapthist

from condor_handler import write_submission_file, exec_submission
from hmax_handler import hmaxoutdir2df
from preproc import add_yborder
from typicality import add_typicalities


def aloi_getpaths(csv_file='/home/contier/ri_hmax/aloi_selection.csv',
                  db='ALOI (2005)',
                  aloi_db_path=pjoin('/home/data/exppsy/object_databases/Datenbanken',
                                     'ALOI_2005',
                                     'png2'),
                  baseworkdir='/home/contier/ri_hmax/workdir/aloi/',
                  rot_stepsize=9,
                  checkexistance=True,
                  overwrite_percepts=False):
    """
    Get a list of IO paths for the ALOI selection. Infiles are specified in the and specified in a csv file.

    Parameters
    ----------
    csv_file : str
        path to csv file containing my selection of ALOi stimuli
    db : str
        For now, only ALOI 2005 works
    aloi_db_path : str
        Path to base directory of the ALOI data base.
    baseworkdir : str
        Path to base of the working directory where prepped and simulated files are to be stored.
    rot_stepsize : int
        Step size for choosing every nth viewpoint from the list of available viewpoints.
    checkexistance : bool
        Check if all generated input files actually exist.
    overwrite_percepts : bool
        if False, only return the input files for which no percepts are generated yet. If True, return all
        input files specified in the csv.

    Returns
    -------
    inpaths : list
        list of absolute paths for all input images.
    preppaths : list
        list of paths for the outputs of preprocessing pipeline
    perceptpaths : list
        list of paths for the outputs of RI simulation
    """
    # create working directories
    for directory in [baseworkdir,
                      pjoin(baseworkdir, 'preprocessed'),
                      pjoin(baseworkdir, 'percepts'),
                      pjoin(baseworkdir, 'hmaxout')]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    # read csv file
    db_df = pd.read_csv(csv_file, sep=';')
    aloi_df = db_df[db_df['database'] == db]
    # get list of file names representing different rotations for each selected stimulus
    inpaths_tmp = [
        pjoin(aloi_db_path, str(db_num), '%s_r%i.png') % (db_num, rotation)
        # there is _r0 to _r355 in steps of 5, yielding  72 images per object. If we take every 9th file, I get 8.
        for rotation in range(0, 360, 5 * rot_stepsize)
        for db_num in aloi_df['db-number']
    ]
    # remove decimal point from float.
    inpaths = [fpath.replace('.0', '') for fpath in inpaths_tmp]

    # check if input files exist
    if checkexistance:
        for infile in inpaths:
            if not os.path.exists(infile):
                raise IOError('Could not find input file : %s ' % infile)

    # create ri simulation output filenames
    perceptpaths = [
        pjoin(baseworkdir, 'percepts',
              inf.split('/')[-1].replace('.png', '_ri_percept.png'))
        for inf in inpaths]

    # re-do inputh and ri_percept paths lists if the respective ri_percept already exists
    if not overwrite_percepts:
        inpaths = [inf for inf, perc in zip(inpaths, perceptpaths) if not os.path.exists(perc)]
        perceptpaths = [pjoin(baseworkdir, 'percepts', inf.split('/')[-1].replace('.png', '_ri_percept.png'))
                        for inf in inpaths]

    # create preprocessing output file names
    preppaths = [
        pjoin(baseworkdir, 'preprocessed',
              inf.split('/')[-1].replace('.png', '_prep.png'))
        for inf in inpaths]
    # create paths for hmax outputs
    intact_hmaxpaths = [
        pjoin(baseworkdir, 'hmaxout',
              prepfile.split('/')[-1].replace('_prep.png', '_intact.ascii'))
        for prepfile in preppaths]
    percept_hmaxpaths = [
        pjoin(baseworkdir, 'hmaxout',
              perceptfile.split('/')[-1].replace('_ri_percept.png', '_percept.ascii'))
        for perceptfile in perceptpaths]

    return inpaths, preppaths, perceptpaths, intact_hmaxpaths, percept_hmaxpaths


def aloi_preproc(imgfile,
                 outfile,
                 saveasuint8=True,
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
    if saveasuint8:
        img_down = img_as_ubyte(img_down)
    # save image
    sio.imsave(outfile, img_down)
    return outfile


def aloi_writesubmit_supersim(inflist,
                              prepflist,
                              perceptflist,
                              runscr,
                              clean=False):
    """
    Write and execute a condor submission file with the IO specified in aloi_getpaths().

    Parameters
    ----------
    inflist, prepflist, perceptflist : lists
        lists containing IO created by aloi_getpaths.
    runscr : str
        path to bash script executed by condor.
    clean : bool
        remove submission file after execution?

    Returns
    -------
    perceptflist : list
        same as input, just passed along for convenience
    """
    submitf = write_submission_file(runscr, inflist, prepflist, perceptflist)
    exec_submission(submit_fpath=abp(submitf), cleanup=clean)
    print('Submitted ALOI selection to condor for simulation with script %s' % runscr)
    return perceptflist


def aloi_writesubmit_hmax(prepfiles, perceptfiles, intactouts, perceptouts,
                          runscr, clean=False):
    # merge input and output lists
    hmaxinputs = prepfiles + perceptfiles
    hmaxoutputs = intactouts + perceptouts

    submitf = write_submission_file(runscr, hmaxinputs, hmaxoutputs)
    exec_submission(submit_fpath=abp(submitf), cleanup=clean)
    print('Submitted ALOI prepped and percept files to condor for HMAXing with %s' % runscr)
    return hmaxinputs, hmaxoutputs


def aloi_hmaxout2df_pickle(hmaxoutdir="/home/contier/ri_hmax/workdir/aloi/hmaxout",
                           pickle_outfile="/home/contier/ri_hmax/workdir/aloi/hmax_df.pickle"):
    """
    Create pandas data frame containing hmax outputs for the selected stimuli from the ALOI library.
    Compute typicalities and save resulting data frame as a pickle file.
    """

    # grab hmax output into data frame
    df = hmaxoutdir2df(hmaxoutdir)
    # compute typicalities and add to data frame
    df = add_typicalities(df, avrg=False)

    # save as pickle file
    with open(pickle_outfile, 'wb') as f:
        pickle.dump(df, f)
    return None
