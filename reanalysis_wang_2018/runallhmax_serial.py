#!/usr/bin/env python


"""
execute 'runhmaxonimages.py'
On a bunch of stimuli in serial fashion.
Here, the stimuli are in two directoreis: ./orig and ./sim.
The results are stored in ./results.
"""

import glob
import os
from os.path import abspath as abp
from os.path import join as pjoin
from subprocess import call

os.chdir('hmax-python')

# get directories
origs = glob.glob('../orig/*')
sims = glob.glob('../sim/*')


def hmax_filelist(filelist):

    for fname in filelist:

        # absolute path names
        fname_abp = abp(fname)
        if 'orig' in fname_abp:
            outname_abp = fname_abp.replace('orig', 'results') + '.ascii'
        elif 'sim' in fname_abp:
            outname_abp = fname_abp.replace('sim', 'results') + '.ascii'

        # call function
        if not os.path.exists(outname_abp):
            call(['python', 'runhmaxonimages.py', '-i', fname_abp, '-o', outname_abp])
        else:
            print('file %s already exists' % outname_abp)


hmax_filelist(origs)
print('hmaxed all originals')

hmax_filelist(sims)
print('hmaxed all simulated images')
