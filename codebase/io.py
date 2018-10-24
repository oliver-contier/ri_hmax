#!/usr/bin/env python

import pandas as pd
from os.path import abspath as abp
from os.path import join as pjoin


def getfiles_aloi_selection(csv_file='stim_selection.csv',
                            db='ALOI 2005)',
                            aloi_db_path='/home/data/exppsy/object_databases/Datenbanken/ALOI (2005)/png2',
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
    filelist : list
        list of absolute paths for all images.
    """
    # Just a reminder, my naming convention for hmax files is: 'apple_1_ri_percept.png.ascii'
    # so in the ALOI case, it works out as something like: dbnum_r360 + vision + .ascii

    db_df = pd.read_csv(csv_file)
    aloi_df = db_df[db_df['database'] == db]

    # get list of file names representing different rotations for each selected stimulus
    filelist = [
        abp(pjoin(aloi_db_path, 'db_num', '%s_r%i.png')) % (db_num, rotation)
        # there is _r0 to _r355 in steps of 5 -> 72 images per object. If we take every 9th file, I get 8.
        for rotation in range(0, 360, 5 * rot_stepsize)
        for db_num in aloi_df['db-number']
    ]
    return filelist


def aloi_selection2percepts(filelist):
    # TODO: run pulse2percept on all images in my aloi selection
    # TODO: accept simulation parameters as args
    pass
