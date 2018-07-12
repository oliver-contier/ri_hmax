import numpy as np
import random
import glob
import cPickle
import scipy.stats.mstats

# Generate the list of HMax output files for distractors and targets, respectively:

dfiles = glob.glob('./AnimalDB/Distractors/*.hmaxout.ascii')
tfiles = glob.glob('./AnimalDB/Targets/*.hmaxout.ascii')

allfiles = dfiles + tfiles

dist=[]

# As in Serre et al. PNAS 2007, we use the pseudo-inverse method for
# classification: 
# We want to find a vector w which, when dot-multiplied with an output vector for an image, gives us the predicted class of the image.
# To do this, we compute the
# pseudo-inverse of the data matrix (i.e. all the output vectors from training
# images stacked as rows) TrainingData^-1, then we compute
# TrainingData^-1*TrainingClasses (the column vector of the classes of all
# training images), which gives us the weights vector w
# (because we want w such that traindata * w = trainingclasses =>
# traindata^-1*traindata*w = traindata^-1*trainingclasses => w =
# traindata^-1*trainingclasses). Then we
# just compute w*output for each output vector of all test images. The sign of
# the result is the predicted class. 


alldata = []
classes=[]


# We extract the data from all the output files in the distractor directory; we
# also append the class for each file ("-1", since they're distractors) to the
# class list
for filename in tfiles:
    data = []
    with open(filename, "rb") as f:
        for line in f:
            data.append(float(line))
    alldata.append(data)
    classes.append(1.0)

# Same thing for distractors (class "-1.0")
for filename in dfiles:
    data = []
    with open(filename, "rb") as f:
        for line in f:
            data.append(float(line))
    alldata.append(data)
    classes.append(-1.0)



# We store the resulting data into a single file, so we don't need to keep the
# output files for each image
with open('hmaxresults.dat', 'wb') as f:
    cPickle.dump(alldata, f, protocol=-1)

# Sanity check! If it still works (score signif. > .5) after uncommenting that,
# you have a problem:
#random.shuffle(classes)

# Not necessary, but it does improve performance somewhat:
alldata = scipy.stats.mstats.zscore(alldata)

# One half of the data used as training data, other half used as test data:
traindata = np.vstack(alldata[1::2])
testdata = np.vstack(alldata[::2])
trainclasses = np.array(classes[1::2])
testclasses = np.array(classes[::2])

# Classification
traindatainv = np.linalg.pinv(traindata)
weights = np.dot(traindatainv, trainclasses)
classifieroutput = np.dot(testdata, weights)
predictedtestclasses = np.sign(classifieroutput)

print "Predicted test classes (ideally, would be one block of ones and another block of minus ones)"
print predictedtestclasses
score =  sum(predictedtestclasses == testclasses) / float(len(testclasses))
print "Score:", score, "("+str(sum(predictedtestclasses == testclasses))+" right out of", \
        str(len(testclasses))+")"



# If saved in the cPickle format (old version):
#dfiles = glob.glob('./AnimalDB/Distractors/*.cpickle')
#tfiles = glob.glob('./AnimalDB/Targets/*.cpickle')
    #with open(filename, "rb") as f:
    #    C2outAllSizes = cPickle.load(f)
    #    C3out = cPickle.load(f)
    #    data = np.append(C3out, [C2bout for C2bout in C2outAllSizes])
    #with open(filename, "rb") as f:
    #    C2outAllSizes = cPickle.load(f)
    #    C3out = cPickle.load(f)
    #    data = np.append(C3out, [C2bout for C2bout in C2outAllSizes])
