import hmaxoptions as opt


import cPickle
import random
import pdb
import numpy as np
import scipy.misc as sm
import scipy.signal
import math
import scipy.ndimage.filters as snf
import os

reload(opt)

np.seterr(all='raise') #Floating point errors generate an actual exception rather than a warning



def buildS1filters():
    """
    This function returns a list of list of S1 (Gabor) filters. Each Gabor
    filter is a square 2D array. The inner
    lists run over orientations (4 orientations per scale), and the outer list
    runs over scales (all the S1 RF sizes defined in the options). We use
    exactly the same equation as in Serre et al. PNAS 2007 (SI text).
    """
    
    print "Building S1 filters"
    filts=[];
    for RFSIZE in opt.S1RFSIZES:
        filtsthissize=[]
        for o in range(0,4):
            theta = o * math.pi / 4
            #print "RF SIZE:", RFSIZE, "orientation: ", theta / math.pi, "* pi"
            x, y = np.mgrid[0:RFSIZE, 0:RFSIZE] - RFSIZE/2
            sigma = 0.0036 * RFSIZE * RFSIZE +0.35 * RFSIZE + 0.18
            lmbda = sigma / 0.8 
            gamma = 0.3
            x2 = x * np.cos(theta) + y * np.sin(theta)
            y2 = -x * np.sin(theta) + y * np.cos(theta)
            myfilt = (np.exp(-(x2*x2 + gamma * gamma * y2 * y2) / (2 * sigma * sigma))
                    * np.cos(2*math.pi*x2 / lmbda))
            #print type(myfilt[0,0])
            myfilt[np.sqrt(x**2 + y**2) > (RFSIZE/2)] = 0.0
            # Normalized like in Minjoon Kouh's code
            myfilt = myfilt - np.mean(myfilt)
            myfilt = myfilt / np.sqrt(np.sum(myfilt**2))
            filtsthissize.append(myfilt.astype('float'))
        filts.append(filtsthissize)
    return filts

def runS1group(imgin, s1f):
    """ 
    We use a special dedicated function for running S1 filters, as opposed
    to other S filters. It might not be strictly necessary, but that's how we
    do it because S1 has special aspects (the input is 2D rather than 3D, the
    filters can get very large, etc.).

    Arguments:
    imgin -- image data, as a 2D array
    s1f -- the S1 filters, in the format produced by buildS1filters()

    Each S1 cell is supposed to multiply its inputs by its filter, and then
    divide the result by the norm of its input (normalized dot-product, AKA
    cosine between inputs and filter - See Kouh 2006, or Jim Mutch's hmin
    code). We do this efficiently by convolving the
    image with each filter, then dividing the results pointwise with the square root of the
    convolution of the squared image with a uniform filter of adequate size (for each scale). 

    Returns a list of 3D arrays (one per S1 scale). Each 3D array is a
    depth-stack of 4 2D maps, one per orientation.

    This function uses Fourier-based convolutions, which help with very large filters. 
    """

    # Note: output is a list of 3D arrays - one per scale.  Each 3D array is
    # a stack of 2D maps, one per orientation/prototype.
    print "Running S1 group"
    img = imgin.astype(float)
    output=[]
    imgsq = img**2
    cpt=0
    # Each element in s1f is the set of filters (of various orientations) for a
    # particular scale. We also use the index of this scale for debugging
    # purposes in an assertion.
    for scaleidx, fthisscale in enumerate(s1f):
        # We assume that at any given scale, all the filters have the same RF size,
        # and so the RF size is simply the x-size of the filter at the 1st orientation
        # (note that all RFs are assumed square).
        RFSIZE = fthisscale[0].shape[0]
        assert RFSIZE == opt.S1RFSIZES[scaleidx]
        outputsAllOrient = []
        # The output of every S1 neuron is divided by the
        # Euclidan norm (root-sum-squares) of its inputs; also, we take the
        # absolute value.
        # As seen in J. Mutch's hmin and Riesenhuber-Serre-Bileschi code.
        # Perhaps a SIGMA in the denominator would be good here?...
        # Though it might need to be adjusted for filter size...
        tmp = snf.uniform_filter(imgsq, RFSIZE)*RFSIZE*RFSIZE
        tmp[tmp<0]=0.0
        normim = np.sqrt(tmp) + 1e-9 + opt.SIGMAS1
        assert np.min(normim>0)
        for o in range(0,4):
            # fft convolution; note that in the case of S1 filters, reversing
            # the filters seems to have no effect, so convolution =
            # cross-correlation (...?)
            tmp = np.fft.irfft2(np.fft.rfft2(img) * np.fft.rfft2(fthisscale[o], img.shape))
            # Using the fft convolution requires the following (fun fact: -N/2 != -(N/2) ...)
            tmp =np.roll(np.roll(tmp,-(RFSIZE/2), axis=1),-(RFSIZE/2), axis=0)
            # Normalization
            tmp  /= (normim)
            fin = np.abs(tmp[RFSIZE/2:-RFSIZE/2, RFSIZE/2:-RFSIZE/2])
            assert np.max(fin) < 1
            outputsAllOrient.append(fin)
        # We stack together the orientation maps of all 4 orientations into one single
        # 3D array, for each scale/RF size.
        output.append(np.dstack(outputsAllOrient[:]));
        cpt += 1
    return output

def runGlobalCgroup(Sinputs):
    """ 
    Returns the list of the maximal activation for each prototype
    (across all positions and scales)  in the incoming S stack. 
    """
    print "Running Global C group (global max of S inputs)"
    outputs=np.zeros(Sinputs[0].shape[2])
    for Sthisscale in Sinputs:
        wdt, lgt, depth = Sthisscale.shape
        # The number of prototypes had better be the same for all scales!
        assert depth == Sinputs[0].shape[2] 
        for p in range(depth):
            outputs[p] = max(outputs[p], np.max(Sthisscale[:,:,p]))
    return outputs                           
            
            

def runCgroup(Sinputs):
    """ Compute the local maxima among cells of neighbouring positions and
    scales and identical orientatio/prototype, over all the maps in the
    incoming S input.

    Argument:
    Sinputs --- A list of 3D arrays, one per scale in the S input.  Each 3D array is
     a stack of 2D maps, one per orientation/prototype of the incoming S input
     (this is the format produced by runSgroup and runS1group).

    The output is a list of 3D arrays, one per scale in the C output. The
    number of outgoing scales is half the number of incoming scales, because
    maps of neighbouring scales are merged. Each 3D array is a depth-stack of
    2D maps, one per orientatio/prototype.
    """

    print "Running C group"
    # In both C1 and C2, RF sizes start at 8 and grow by 2s
    Cscale = 8
    output = []
    # for every OTHER scale in the Sinputs...
    for k in range(0, len(Sinputs), 2):
        #print "Using / merging S input scales "+str(k)+" and "+str(k+1)
        wdt, hgt, depth = Sinputs[k].shape
        # depth is the number of orientations/prototypes
        # We want to resize the next scale map to have the same size as the
        # current one (which should be larger since it has lower RF size)
        outperp=[]
        for p in range(depth):
            # The spatial sampling rate is determined by the scale / RF size:
            epsilon = Cscale - 5
            img1 = Sinputs[k][:,:,p]
            if k+1 < len(Sinputs):
                # The 'F' is crucial, otherwise imresize forces the output 
                # as int8!
                img2 = sm.imresize(Sinputs[k+1][:,:,p], (wdt, hgt), mode='F', interp='bicubic')
            else:
                # If there is no "next scale" (od number of scales),
                # we duplicate the current scale as a "dummy"  -
                # wastes time, but simplifies code
                img2 = img1
            maxfilteroutput = snf.maximum_filter(np.dstack((img1, img2)), size=(Cscale,Cscale,2))
            outperp.append(maxfilteroutput[::epsilon,::epsilon,1])
        output.append(np.dstack(outperp[:]))
        Cscale += 2
    return output

def myNormCrossCorr(stack, prot):
    """ This helper function performs a 3D cross-correlation between a 3D stack
    of 2D maps (stack) and a 3D prototype (prot). These have the same depth,
    and we exclude the edges, so only one 2D map is produced. 

    This is done by summing shifted versions of the input stack, multiplied by
    the appropriated value of the prototype.
    
    This method is much faster than anything else (including FFT convolution)
    due to the fact that the majority of weights are set to -1 (i.e. "ignore"),
    following Serre (see extractCpatch()).
    
    For normalization, we also sum shifted versions of the input stack,
    squared. We then divide the output of the cross-correlation with the square
    root of this map. Again, this is equivalent to multiplying the prots by the
    inputs at each point, then dividing the result by the norm of the inputs,
    following Kouh's method.

    """

    assert prot.shape[2] == stack.shape[2]
    NBPROTS = prot.shape[2]
    RFSIZE = prot.shape[0] # Assuming square RFs, always
    zerothres = RFSIZE*RFSIZE * (-1)
    #cpt = 0 # For debugging
    XSIZE = stack.shape[0]
    YSIZE = stack.shape[1]
    norm = np.zeros((XSIZE-RFSIZE+1, YSIZE-RFSIZE+1))
    o2 = np.zeros((XSIZE-RFSIZE+1, YSIZE-RFSIZE+1))
    for k in range(NBPROTS):
# If all the weights in that slice of the filter are set to -1, don't bother (note
# that this will be the case for >90% of slices in S3):
        if np.sum(prot[:,:,k]) > zerothres:
            for i in range(RFSIZE):
                for j in range(RFSIZE):
                    if prot[i,j,k] > 0: #> 1e-7:
                        #cpt += 1
                        norm += stack[i:i+1+XSIZE-RFSIZE, j:j+1+YSIZE-RFSIZE, k] ** 2
                        o2  +=  stack[i:i+1+XSIZE-RFSIZE, j:j+1+YSIZE-RFSIZE, k] * prot[i,j,k]
    return o2 / (np.sqrt(norm + 1e-9) + opt.SIGMAS)



def runSgroup(Cinputs, prots):
    """ Run the S filters (contained in prots) over the output of a previous C group (Cinputs)

    Arguments:
    Cinputs -- a list of 3D arrays - one per scale, the output of the previous
    C group. Each 3D array is a stack of N_P 2D layers, one per orientation/prototype
    of the previous C layers (the same format as produced by runCgroup). 
    prots -- the list of prototypes for this S group, each of which is a
    NxNxN_P, which we 3D-cross-correlate with the stacks of Cinputs,  and do it
    successively for all scales.

    The output is a list of 3D arrays (one per scale). Each 3D array is a
    depth-stack of 2D maps, one per prototype in the prots stack. There are as
    many scales as in the C input, and as many prototypes as contained in
    prots.
    """
    print "Running S group (corr), RF size ", prots[0].shape[0], " Cin depth ", Cinputs[0].shape[2]
    output=[]
    # For each scale, extract the stack of input C layers of that scale...
    for  Cthisscale in Cinputs:
        # If the C input maps are too small, as in, smaller than the S filter,
        # then there's no point in computing the S output; we return a depth-column 
        # of 0s instead
        # Note that we're assuming all the prototypes to have the same size
        if prots[0].shape[0] >= Cthisscale.shape[0]:
            outputthisscale = [0] * len(prots)
            output.append(np.dstack(outputthisscale[:]))
            continue
        
        outputthisscale=[]
        for nprot, thisprot in enumerate(prots):
            # Filter cross-correlation !
            tmp = myNormCrossCorr(Cthisscale, thisprot)         
            outputthisscale.append(tmp)
            assert np.max(tmp) < 1
        output.append(np.dstack(outputthisscale[:]))
    return output


def extractCpatch(Cgroup, RFsize, nbkeptweights, ispatchzero=False):
    """ 
    This helper function is the core of buildS2prots() and buildS3prots(). It
    extracts patches from stacks of C layers, to use as prototypes for the S
    layers.
    
    Cgroup is a group of C stacks (one per scale). Each C stack is a stack of C
    maps (one per orientation [for C1] or prototype [for C2]). The patches
    Extracted are basically 3D chunks of this 3D stack, normalized (i.e.
    divided pointwise by the total norm of the patch).

    RFsize is the desired size of the patches in the map plane (in the 3rd
    dimension, the size is determied by the number of orientations/prototypes).

    nbkeptweights is the number of values within the patch to use as actual
    weights. All other ones will be set to -1, corresponding to "ignore" (following Serre).

    ispatchzero is an optional parameter for debugging purposes (see code).
    """

    # If the C stack of the lowest scale (i.e. the one with the larger maps) 
    # has dimensions smaller than the RF size, there's no point going on - use larger images!
    assert Cgroup[0].shape[0] > RFsize
    # Let's find a scale for which the map sizes are larger than the requested RF size
    while True:
        Cchoice = random.choice(Cgroup)
        if Cchoice.shape[0] > RFsize:
            break
    posx = random.randrange(Cchoice.shape[0] - RFsize)
    posy = random.randrange(Cchoice.shape[1] - RFsize)
# This is for debugging - we want the first patch of the first scale of each S group to 
# be at the center of the input image (which will be lena.png), so we can check that when
# running the model on lena.png, the maximum for this prototype and scale will be at the
# center (otherwise, problem!)
    #if ispatchzero:
    #    Cchoice = Cgroup[0]
    #    posx = Cchoice.shape[0]/2 - RFsize/2
    #    posy = Cchoice.shape[1]/2 - RFsize/2
    prot = Cchoice[posx:posx+RFsize,posy:posy+RFsize,:]
# We only keep 'nbkeptweights' weights and set all other weights to -1
    permutedweights = np.random.permutation(prot.size)
    keptweights = permutedweights[:nbkeptweights]
    zeroedweights = permutedweights[nbkeptweights:]

    # Here, for normalization, we just need to compute the norm of
    # a single patch, so we don't need to go through the
    # uniform_filter of the squared input thing...
    # Of course only use kept weights in the normalization
    prot = prot / np.linalg.norm(prot.flat[keptweights])
    # Set non-kept weights to -1 - *after* normalizing...
    prot.flat[zeroedweights] = -1
    return prot



def buildS2prots(numprots, reqnbkeptweights, reqRFsize, v1filters):
    """ 
    Build S2 or S2b prototypes by extracting C1 output patches, using images in
    the "images" directory.

    numprots -- the number of prototypes to extract.

    reqnbkeptweights -- the number of weights to conserve (Serre uses 10, see
    buildandsaveallfilts()).

    reqRFsize -- the RF size (3 for S2, various for S2b).

    v1filters -- the S1 filters, as produced by
    buildS1filters(). 
    """
    print "Building S2 prototypes (RF size ", reqRFsize, ")"
    imgfiles = os.listdir("images")
    prots=[]
    for n in range(numprots):
        print "S2 prot. ", n, " (RF size ", reqRFsize, ")"
# Read natural image data...
        imgfile = random.choice(imgfiles)
        #NOTE: Should include something here to fail gracefully if a non-image file is encountered
        img = sm.imread(opt.ImagesForProtsDir+'/'+imgfile)
# For debugging:
        #if n==0:
        #    img = sm.imread('lena.png')
            
        S1out = runS1group(img, v1filters)
        C1out = runCgroup(S1out)
        prots.append(extractCpatch(C1out, RFsize=reqRFsize, 
                    nbkeptweights=reqnbkeptweights, ispatchzero=(n==0)))
    return prots
       
def buildS3prots(numprots, reqnbkeptweights, reqRFsize, v1filters, s2filters):
    """ 
    Build S3 prototypes by extracting C2 output patches, using images in the "images" directory.

    numprots -- the number of prototypes to extract.

    reqnbkeptweights -- the number of weights to conserve (Serre uses 10, see
    buildandsaveallfilts()).

    reqRFsize -- the RF size (3 in Serre).

    v1filters -- the S1 filters, as produced by
    buildS1filters() or loadallfilts(). 
    
    s2filters -- the S2 filters, as produced by
    buildS2prots() or loadallfilts(). 
    """
    print "Building S3 prototypes (RF size ", reqRFsize, ")"
    imgfiles = os.listdir("images")
    prots=[]
    for n in range(numprots):
        print "S3 prot. ", n, " (RF size ", reqRFsize, ")"
        imgfile = random.choice(imgfiles)
# Reading data from natural image file...
        img = sm.imread(opt.ImagesForProtsDir+'/'+imgfile)
# For debugging:
        #if n==0:
        #    img = sm.imread('lena.png')
            
        S1out = runS1group(img, v1filters)
        C1out = runCgroup(S1out)
        S2out = runSgroup(C1out, s2filters)
        C2out = runCgroup(S2out)
        prots.append(extractCpatch(C2out, RFsize=reqRFsize, 
            nbkeptweights=reqnbkeptweights, ispatchzero=(n==0)))
    return prots
       
def buildandsaveallfilts(filename="filters.dat"):
    """ 
    Build and save the filters/prototypes for S1, S2 and S3. The file created
    by this process is read by loadallfilters().
    
    WARNING: Using the Serre parameters, this takes a lot of time (~10 hours!)

    """ 
    filtersfile = open(filename, 'wb')
    v1f = buildS1filters()
    cPickle.dump(v1f, filtersfile)
    s2f = buildS2prots(numprots=opt.NBS2PROTS, reqnbkeptweights = opt.NBKEPTWEIGHTSS2,
        reqRFsize=3, v1filters=v1f)
    cPickle.dump(s2f, filtersfile, protocol=-1)
    S2bfiltersAllSizes=[]
    for s in opt.S2bRFSIZES:
        S2bfiltersAllSizes.append(buildS2prots(numprots=opt.NBS2bPROTS, 
            reqnbkeptweights=opt.NBKEPTWEIGHTSS2B, reqRFsize=s, v1filters=v1f))
	# Format of S2bfiltersAllSizes:
	# List of opt.S2bRFSIZES lists of h.NBS2bPROTS prototypes. Each prototype is
	# an RFSIZE x RFSIZE x 4 array
    cPickle.dump(S2bfiltersAllSizes, filtersfile, protocol=-1)
    cPickle.dump(buildS3prots(numprots=opt.NBS3PROTS, reqnbkeptweights=opt.NBKEPTWEIGHTSS3,
        reqRFsize=3, v1filters=v1f, s2filters=s2f), filtersfile, protocol=-1)
    filtersfile.close()


def loadallfilts(filename='filters.dat'):
    """ 
    Load all the filters (S1, S2, S2b, S3) from a file (default: 'filters.dat').

    The output is a tuple of  filter lists, in the appropriate format for each group. 
    """

    filtersfile = open('filters.dat', 'rb')
    v1f = cPickle.load(filtersfile)
    s2filters=cPickle.load(filtersfile)
    S2bfiltersAllSizes=cPickle.load(filtersfile)
    s3filters=cPickle.load(filtersfile)
    filtersfile.close()
    return (v1f, s2filters, S2bfiltersAllSizes, s3filters)


def hmax(imagedata, v1filters, s2filters, s2bfiltersallsizes, s3filters):
    """ 
    Run the model.

    Arguments:
    imagedata -- the image data as a 2D array

    v1filters, s2filters, s2bfiltersallsizes, s3filters -- the
    filters/prototypes, in the format produced by buildandsaveallfilts() and
    loadallfilts(), and used by runSgroup() and runS1group().

    v1filters is a list of lists of 2D arrays. Each 2D array is a Gabor
    filter. The inner list runs over 4 orientations, while the outer list runs
    over scales (see buildS1filters()).

    s2filters is a list of S2 prototypes, each of which is a 3D array (RF size
    x RF size x 4 orientations)

    s2bfiltersallsizes is a list of lists of S2b prototypes. The inner lists run ov

    """

    S1out = runS1group(imagedata, v1filters)
    C1out = runCgroup(S1out)
    S2out = runSgroup(C1out, s2filters)
    C2out = runCgroup(S2out)
    C2boutallsizes=[]
    for s2bf in s2bfiltersallsizes:
        S2bout = runSgroup(C1out, s2bf)
        C2boutallsizes.append(runGlobalCgroup(S2bout))
    S3out = runSgroup(C2out, s3filters)
    C3out = runGlobalCgroup(S3out)
    return (C2boutallsizes, C3out)



