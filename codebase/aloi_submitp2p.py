#!/usr/bin/env python

from aloi_handler import getfiles_aloi_selection, aloi_selection2percepts

if __name__ == '__main__':
    print('grabbing input images')
    filelist = getfiles_aloi_selection()
    print('submitting p2p simulation to condor')
    outlist = aloi_selection2percepts()
    print('done')
