#!/usr/bin/env python

import os
from os.path import join as pjoin
from subprocess import call


def write_submission_file(runscript,
                          infiles,
                          outfiles):
    """
    Write a condor submission file to run each input image simulation in a seperate job.
    """
    submit_fpath = pjoin(os.getcwd(), 'submit_all.submit')

    # file header
    if '/' in runscript:
        # if path is specified, remove everything but file name
        header_scriptname = runscript.split('/')[-1]
    else:
        header_scriptname = runscript
    headerlines = ["Universe = vanilla",
                   "Executable = %s" % header_scriptname,
                   "Log = %s.log" % header_scriptname,
                   "Output = %s.out" % header_scriptname,
                   "Error = %s.error" % header_scriptname]

    with open(submit_fpath, 'w') as f:
        for line in headerlines:
            f.write(line + '\n')

        # write i/o argument lines
        for infile, outfile in zip(infiles, outfiles):
            f.write("Arguments = %s %s" % (infile, outfile) + '\nQueue\n')
    return submit_fpath


def exec_submission(submit_fpath):
    call(['condor_submit', submit_fpath])
