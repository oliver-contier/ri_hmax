#!/usr/bin/env python

import os
from os.path import join as pjoin
from subprocess import call


def write_submission_file(runscript,
                          arglist1,
                          arglist2):
    # TODO: add static args that don't iterate
    """
    Write a condor submission file to run each input image simulation in a seperate job.

    Parameters
    ----------
    runscript : str
        target script executed by condor. Typically a bash or python script that contains whatever you want to run.
    arglist1 : list
        list of first input arguments that condor should iterate over.
    arglist2 : list
        list of second input arguments that are also iterated.

    Returns
    -------
    submit_fpath : str
        path to the generated .submit file.
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
        for infile, outfile in zip(arglist1, arglist2):
            f.write("Arguments = %s %s" % (infile, outfile) + '\nQueue\n')
    return submit_fpath


def exec_submission(submit_fpath,
                    cleanup=False):
    """
    execute condor submission file

    Parameters
    ----------
    submit_fpath : str
        path to .submit file
    cleanup : bool
        delete submission file after execution?

    Returns
    -------

    """
    call(['condor_submit', submit_fpath])
    if cleanup:
        os.remove(submit_fpath)
