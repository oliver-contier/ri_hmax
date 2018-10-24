#!/usr/bin/env python


import sys

from p2p_handler import img2percept, save_percept

"""
run this script via condor to parallelize p2p simulations for all ALOI files.
"""

if __name__ == '__main__':
    # grab input and output image names
    inf = sys.argv[1]
    outf = sys.argv[2]

    percept = img2percept(inf, naxons=2000)
    save_percept(percept, outfile=outf)
