#!/usr/bin/env python


import glob
from os.path import join as pjoin


def get_flist(basedir):
    """
    Create list of input files.
    """
    flist_orig = glob.glob(pjoin(basedir, 'orig'))
    flist_sim = glob.glob(pjoin(basedir, 'sim'))
    flist = flist_orig + flist_sim
    return flist


def write_submission_file(infiles):
    """
    Write a submission file
    """
    submit_fpath = pjoin(basedir, 'submit_all.submit')
    with open(submit_fpath, 'w') as f:
        # write header
        headerlines = ["Universe = vanilla",
                       "Executable = ../hmax-python/runhmaxonimages.py",
                       "Log = submit_all.log",
                       "Output = submit_all.out",
                       "Error = submit_all.error"]
        for line in headerlines:
            f.write(line + '\n')
        # write i/o argument lines
        for infile in infiles:  #TODO
            f.write("Arguments = %s" % infile + '\nQueue\n')
    return submit_fpath


def exec_submission(submit_fpath):
    call(['condor_submit', submit_fpath])


if __name__=='__main__':

    import sys

    basedir = os.path.abspath(sys.argv[1])
    flist = get_flist(basedir)
    submit_file = write_submission_file(flist)
    exec_submission(submit_file)
