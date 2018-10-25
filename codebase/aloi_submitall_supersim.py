#!/usr/bin/env python

from condor_handler import write_submission_file, exec_submission
from aloi_handler import getfiles_aloi_selection, aloi_selection2percepts


infiles = getfiles_aloi_selection()
outfiles = aloi_selection2percepts(infiles, clean=False, runscr='supersim_runscript.sh')

