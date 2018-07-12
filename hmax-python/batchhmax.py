import sys
import glob
import os
import time


dfiles = glob.glob('./AnimalDB/Distractors/*.jpg')
tfiles = glob.glob('./AnimalDB/Targets/*.jpg')

allfiles = dfiles + tfiles

# Note: about 2 minutes per image, 1200 images in total
chunksize = 50
pos = 0
numchunk = 0
while pos < len(allfiles):
    fileslist = " ".join(allfiles[pos:pos+chunksize])
    mycommand = "bsub -oo output_chunk"+str(numchunk)+".txt -eo error_chunk"+str(numchunk)+".txt -q short -W 5:00 python  runhmaxonimages.py " + fileslist
    os.system(mycommand)
    print "Submitting command: "+mycommand
    print "==="
    pos += chunksize
    numchunk += 1
    #if pos> chunksize*2.5:
    #    break
    time.sleep(3)


