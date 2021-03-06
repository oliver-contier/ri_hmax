#!/usr/bin/env python

import glob
from os.path import abspath as abp
from os.path import join as pjoin
from subprocess import call

import numpy as np
import pandas as pd


def hmax_image(image_infile, hmax_outfile,
               hmax_python_dir=pjoin('..', 'hmax-python')):
    """
    Run python-hmax on a single image.

    :param image_infile : str. path to input image file
    :param hmax_outfile: str. path to output hmax file. Note that file suffix must be '.ascii'
    :param hmax_python_dir:
    :return: outfile. str. Same as the input argument 'outfile' but returned for convenience in file handling later.
    """

    # get absolute path of in and out file
    infile_abs, outfile_abs = abp(image_infile), abp(hmax_outfile)
    # get absolute path to script with hmax python implementation
    script_abs = abp(pjoin(hmax_python_dir, 'runhmaxonimages.py'))
    # call pre-implemented hmax-python
    call(['python', script_abs, '-i', infile_abs, '-o', outfile_abs])
    return hmax_outfile


def hmaxfile2dict(hmax_file):
    """
    read a given output file returned by python-hmax and store its information in a dict.
    stim name, category name, vision type must be indicated by file name (e.g. 'apple_1_percept.png.ascii')

    :param hmax_file: str. path to .ascii file returned by python-hmax
    :return: pattern_dict. dict. contains stimulus name, category name, response pattern, and vision type
    """

    # in case of aloi stimuli, it looks like this:
    # /home/contier/ri_hmax/workdir/aloi/hmaxout/490_r90_percept.ascii

    # get hmax output vector
    hmax_df = pd.read_csv(hmax_file, header=None)
    pattern = np.array([row[0] for row in hmax_df.values])

    # removes all of path except name of the .ascii file, withoug suffix
    fname_nopath = hmax_file.split('/')[-1].replace('.ascii', '')
    # get stimulus name, category name, and vision
    catname, exemplar, vision = fname_nopath.split('_')[0:3]
    if vision == 'percept':
        vision = 'ri_' + vision

    # stimname = hmax_file.replace('.png', '')
    # for substring, vision in zip(['percept', 'intact'], ['ri_percept', 'intact']):
    #     if substring in hmax_file:
    #         vision = vision
    #         stimname = hmax_file.replace('_' + substring, '')  # result should be 'apple_1'
    # catname = stimname.split('_')[0]  # result should be 'apple'

    # create file specific dict
    pattern_dict = {
        'pattern': pattern,
        'category': catname,
        'exemplar': exemplar,
        'vision': vision,
        'filename': abp(hmax_file)
    }
    return pattern_dict


def hmaxoutdir2df(hmax_out_dir):
    """
    Use read_hmax_file function to import all output files in a given directory into single data frame.
    File names must indicate the category (e.g. 'apple') with a number designating a specific exemplar of that
    category (e.g. 'apple_1') and the type of vision ('ri_percept' vs. 'intact').
    Example file name: '/hmax_out_dir/apple_1_ri_percept.png.ascii'.

    :param hmax_out_dir: str
        Directory containing all output files created by python-hmax.
    :return: pattern_df: Data Frame
        Columns are 'category', 'exemplar', 'ri_pattern', 'intact_pattern'
    """
    # Construct list of dicts containing information about our HMAX outputs.
    pattern_dicts = [hmaxfile2dict(hmax_file)
                     for hmax_file
                     in glob.glob(pjoin(hmax_out_dir, '*'))]

    # Assert if all pattern vectors have same length
    first_len = len(pattern_dicts[0]['pattern'])
    if not all(len(pattern) == first_len for pattern in [patterndict['pattern'] for patterndict in pattern_dicts]):
        raise ImportError('Whoops. Not all response vectors of the input files have the same length.')

    # combine all dicts into pandas data frame
    pattern_df = pd.DataFrame(pattern_dicts)
    # tease apart into ri_df and intact_df
    ri_df = pattern_df[pattern_df.vision == 'ri_percept']
    intact_df = pattern_df[pattern_df.vision == 'intact']
    # rename pattern column inti ri_pattern and intact_pattern
    ri_df = ri_df.rename(index=str, columns={'pattern': 'ri_pattern'})
    intact_df = intact_df.rename(index=str, columns={'pattern': 'intact_pattern'})
    # drop vision and file name columns from both dfs
    ri_df = ri_df.drop(columns=['filename', 'vision'])
    intact_df = intact_df.drop(columns=['filename', 'vision'])
    # merge the two DFs
    object_df = pd.merge(ri_df, intact_df, on=['category', 'exemplar'])

    return object_df


if __name__ == '__main__':
    """
    this script can also be executed via the runscript triggered through condor to run hmax model on an individual
    image.
    """
    import sys

    infile = sys.argv[1]
    outfile = sys.argv[2]

    hmax_image(infile, outfile, hmax_python_dir=pjoin('..', 'hmax-python'))
