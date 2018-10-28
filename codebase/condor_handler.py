#!/usr/bin/env python

import os
from os.path import join as pjoin
from subprocess import call


def write_submission_file(runscript, *arg_lists):
    """
    Write a condor submission file to iterate over lists of arguments.

    # TODO: add static args that don't iterate
    # TODO: assert all arglists have same length

    Parameters
    ----------
    runscript : str
        target script executed by condor. Typically a bash or python script that contains whatever you want to run.
    *arg_lists : list
        list of argument lists. each of those argument lists will be iterated over.
        example: [[1,2], [3,4], [5,6]] will produce lines like
                Arguments = 1 3 5
                Queue
                Arguments = 2 4 6
                Queue
    Returns
    -------
    submit_fpath : str
        path to the generated .submit file.
    """
    # just slab the submission file into the current working directory
    submit_fpath = pjoin(os.getcwd(), 'submit_all.submit')

    # shorten runscript name if whole path is given
    if '/' in runscript:
        # if path is specified, remove everything but file name
        header_scriptname = runscript.split('/')[-1]
    else:
        header_scriptname = runscript

    # define header
    headerlines = ["Universe = vanilla",
                   "Executable = %s" % header_scriptname,
                   "Log = %s.log" % header_scriptname,
                   "Output = %s.out" % header_scriptname,
                   "Error = %s.error" % header_scriptname]

    with open(submit_fpath, 'w') as f:
        # write header
        for line in headerlines:
            f.write(line + '\n')
        # write arguments
        for idx in range(len(arg_lists[0])):
            selected_args = [str(arglist[idx]) for arglist in arg_lists]
            args_string = ' '.join(selected_args)
            f.write('Arguments = ' + args_string + '\nQueue\n')

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
