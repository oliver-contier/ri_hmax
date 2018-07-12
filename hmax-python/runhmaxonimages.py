import traceback
import sys
import cPickle
import hmax
import scipy.misc
import numpy
import time

reload(hmax) 

print "Loading all filters" 
(v1f, s2f, s2bfAllSizes, s3f) = hmax.loadallfilts()

if len(sys.argv) < 2:
    raise StandardError("Pass the filenames of the images as arguments")


for filename in sys.argv[1:]:
    try:

        print "Processing image "+filename
        img = scipy.misc.imread(filename)
# If there are more than 2 dimensions, the 3rd one (presumably RGB) is 
# averaged away to obtain a 2D grayscale image:
        if len(img.shape) > 2:
            img = numpy.mean(img, axis=2)

        t = time.time()
        (C2boutAllSizes, C3out) = hmax.hmax(img, v1f, s2f, s2bfAllSizes, s3f)
        print "Time elapsed:", (time.time()-t)
        with open(filename+'.hmaxout.ascii', 'wb') as f:
            f.writelines([str(x)+"\n" for EachRFsize in C2boutAllSizes for x in EachRFsize])
            f.writelines([str(x)+"\n" for x in C3out])
    
    except Exception as e:
        print e
        traceback.print_exc()
        print "Unexpected error"

        
# Old version (cPickle format):
#with open(filename+'.hmaxout.cpickle', 'wb') as f:
   #cPickle.dump(C2boutAllSizes, f, protocol=-1)
   #cPickle.dump(C3out, f, protocol=-1)


