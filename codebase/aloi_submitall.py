#!/usr/bin/env python

from aloi_handler import aloi_getpaths, aloi_writesubmit_supersim, aloi_writesubmit_hmax

if __name__ == '__main__':
    import sys

    # execute this script with argument 'supersim' or 'hmax' to decide the operation you want to submit to condor.
    decision = sys.argv[1]

    # get file names
    infiles, prepfiles, perceptfiles, intacthmaxfiles, percepthmaxfiles = aloi_getpaths()

    if decision == 'supersim':
        outfiles = aloi_writesubmit_supersim(infiles, prepfiles, perceptfiles, 'supersim_runscript.sh', clean=False)
    if decision == 'hmax':
        aloi_writesubmit_hmax(prepfiles, perceptfiles, intacthmaxfiles, percepthmaxfiles,
                              'hmax_runscript.sh', clean=False)
    else:
        raise IOError("Sorry, I don't know the argument %s" % decision)
