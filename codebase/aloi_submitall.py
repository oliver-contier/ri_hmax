#!/usr/bin/env python

import sys
import os

from aloi_handler import aloi_getpaths, aloi_writesubmit_supersim, aloi_writesubmit_hmax

if __name__ == '__main__':

    # execute this script with argument 'supersim' or 'hmax' to decide the operation you want to submit to condor.
    decision = sys.argv[1]

    if decision == 'supersim':
        overwrite = False
    else:
        overwrite = True

    # get file names
    infiles, prepfiles, perceptfiles, intacthmaxfiles, percepthmaxfiles = aloi_getpaths(overwrite_percepts=overwrite)

    # write and execute supersim
    if decision == 'supersim':
        outfiles = aloi_writesubmit_supersim(infiles, prepfiles, perceptfiles,
                                             'supersim_runscript.sh', clean=False)
    print('\nnumber of grabbed input file names : %i.\nAll others already exist.' % len(infiles))

    # write and execute hmax
    if decision == 'hmax':
        # check existance of intact (prepped) and ri percept files
        for filelist in [prepfiles, perceptfiles]:
            for targetf in filelist:
                if not os.path.exists(targetf):
                    raise IOError('could not find file %s ' % targetf)
        aloi_writesubmit_hmax(prepfiles, perceptfiles, intacthmaxfiles, percepthmaxfiles,
                              'hmax_runscript.sh', clean=False)

    elif decision not in ['supersim', 'hmax']:
        raise IOError("Sorry, I don't know the argument %s" % decision)
