"""
Modified version of the python HMAX implementation by Thomas Miconiself.
Original version was retrieved from https://scholar.harvard.edu/tmiconi/pages/code on July 10th 2018self.
"""


import traceback
import sys
import cPickle
import hmax
from imageio import imread
import numpy
import time

reload(hmax)

print "Loading all filters"
(v1f, s2f, s2bfAllSizes, s3f) = hmax.loadallfilts()


"""
Parse command line arguments
"""

print('parsing command line arguments')

import argparse
parser = argparse.ArgumentParser(prog='runhmaxonimages.py',
                                 description=__doc__)
parser.add_argument('-i', required=True, dest='infile')
parser.add_argument('-o', required=True, dest='outfile')
args = parser.parse_args()
infile = args.infile
outfile = args.outfile

# assert input and output names
if not infile or not outfile:
    raise IOError('Input and/or output not specified.\n')
if not outfile.split('.')[-1] == 'ascii':
    raise IOError('Output file name must end in ".ascii"')

"""
Actual HMAXing
"""

print "Processing image %s" % infile
img = imread(infile)

# If there are more than 2 dimensions, the 3rd one (presumably RGB) is
# averaged away to obtain a 2D grayscale image:
if len(img.shape) > 2:
    img = numpy.mean(img, axis=2)

t = time.time()
(C2boutAllSizes, C3out) = hmax.hmax(img, v1f, s2f, s2bfAllSizes, s3f)
print "Time elapsed:", (time.time()-t)

"""
Write output
"""

with open(outfile, 'wb') as f:
    f.writelines([str(x)+"\n" for EachRFsize in C2boutAllSizes for x in EachRFsize])
    f.writelines([str(x)+"\n" for x in C3out])


print('Produced output: %s' % outfile)
