#!/usr/bin/env python

from os.path import abspath as abp
from os.path import join as pjoin

import pandas as pd

from condor_handler import write_submission_file, exec_submission
from hmax_handler import hmax_image


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


def aloi_selection2percepts(inflist,
                            runscr='aloi_condor_runscript.py',
                            workdir='~/ri_hmax/workdir/'):
    # TODO: accept simulation parameters as args
    """
    """
    """
    2. use those to create a condor submission file and execute it
    3. print statements to check submission status
    4. return list of outfile names
    """
    outflist = [pjoin(workdir, inf.replace('.png', 'ri_percept.png'))
                for inf in inflist]
    submitf = write_submission_file(runscript=runscr, infiles=inflist, outfiles=outflist)
    exec_submission(submit_fpath=abp(submitf))
    print('Submitted ALOI selection to condor for p2p simulation')
    return outflist


# TODO: Function to run python-hmax on my ALOi selection
"""
hmax_outputs = [hmax_image(imgin, hmaxout, hmax_python_dir=pjoin('~', 'ri_hmax', 'hmax-python'))
                for imgin, hmaxout in zip(inflist, outflist)]
"""