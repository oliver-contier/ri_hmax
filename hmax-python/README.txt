Introduction
===

This is an implementation of the HMax model of visual recognition recognition.
The implementation mostly follows Serre, Oliva and Poggio, PNAS 2007, except
that the simple cells' tuning operation is a semi-normalized dot product as in
Minjoon Kouh's PhD thesis (see Implementation details, below).

All you need to run this code is a working python interpreter, with the numpy
and scipy libraries installed.

To run the model, after unzipping the files, just type:

    python runhmaxonimages.py imagefile1 imagefile2....

where imagefile1, imagefile2, etc. are the filenames (with full paths) of the
image files that you want to run the model on.

It may help if you use grayscale images only.

NOTE: depending on your platform and interpreter, you might need to use "python
-c ./runhmaxonimages.py imgfile" or "python -c .\runhmaximages.py imgfile"
instead.

On a recent machine, the code takes about a minute to run on a 256x256 image.

This will produce one output file per image. The output file will be named
"imagefile1.hmaxout.ascii", etc. and will be located in the same directory as the
original image file. This output file contains a list of floating-point values, stored in
ascii format for maximal portability. These values are the output of the C2b
cells (over successive RF sizes) and C3 cells, in that order.

You can then run whatever classification program you want on these outputs.

The included classifyhmaxoutputs.py is a program that runs a simple binary
classification on output files, using one half of the data for training and the
other half for testing. It assumes that the two classes of images are located
in the "./AnimalDB/Distractors" and "./AnimalDB/Targets" directory,
respectively - because it was set up to work on the AnimalDB images for
Animal/Non-animal classification task, as used in Serre et al. PNAS 2007. Just
modify the two corresponding lines of code to make it read output files from any
directories you like.

As it is, the code produces 77% correct classification of test images in
AnimalDB (chance level 50%).

The parameters of the experiment are defined in hmaxoptions.py. These include:
- The RF sizes of different S1 scales
- The RF sizes of different S2b groups
- The number of S2, S2b and S3 prototypes (for S2b, this number applies to each RF size)
- The 'sigmas' (additive constant in the normalization denominator) for S1 and for the other S layers


Files and code organization
===

The actual model implementation is the hmax.py module. Other files are either
data files or helper programs that apply the model or process its outputs.

The included files are:

- hmax.py: The model implementation.

- hmaxoptions.py: Various model parameters.

- filters.dat: The file that contains the data for the various filters and
  prototypes of simple cells. You will need to re-build this if you want to use
  different parameters (see below).

- runhmaxonimages.py: Uses the hmax module to run the full HMax model on a set
  of image files given as parameters (see above). Requires all the files
  mentioned above.

- classifyhmaxoutputs.py: Performs a simple binary classification on model
  outputs to test performance (see above).

- batchhmax.py: A convenience program that divides the set of image files found
  in given directories into chunks, and submits runhmaxonimages.py with each
  chunk to a batch processing cluster (LSF, but you can adapt it by modifying
  the submission line in the code)

The main function of the hmax module is the 'hmax' function. Its entire code is as
follows:

def hmax(imagedata, v1filters, s2filters, s2bfiltersallsizes, s3filters):
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

The arguments are the data structures that contain the image data (a 2D array
of floating point luminance values) and the various filters and prototypes (in
the same format produced by buildandsaveallfilts() or loadallfilts() in the
hmax.py module).

As can be seen from the code, the function simply applies successive S and C
operations. Note that S1 has its own runS1group function. For S2b, the S and C
operations are applied separately for each RF size. The output is the set of
C2b values (a list of list, one per RF size) and of C3 values (a single list).

Note that some debugging code has been left in the module, although commented
out. E.g. there is code to ensure the first prototype of all S groups is
extracted from the center of the 'lena.png' image - if you set all 'sigma's to
0, the maximum activation for these prototypes when applied to lena.png should
then be at the center, and produce a value of 1 (or very close to it, due to
the minimal additive constant in the normalization to prevent division by
zero). You might find it useful if you want to modify the code.


Building prototypes
===

HMax 'simple' cells rely on prototypes/filters with which they compare their
inputs. These are stored in filters.dat. You can build your own filters/prototypes, using
your own set of natural images, with the buildandsaveallfilts() function in
the hmax.py module. Note that you will need to do this if you want to modify
any parameter. The directory containing the natural images to be used for
prototype extraction is specified in hmaxoptions.py.



Implementation details
====

The implementation largely follows Serre, Oliva and Poggio, PNAS 2007. The main
difference is that the simple cells do not compare their inputs with their
prototypes using a Gaussian tuning; rather, they use a semi-normalized
dot-product, that is, a dot-product between prototype and inputs, divided by
the norm of the inputs (plus a fixed additive constant, hence the 'semi-'), as
seen in Minjoon Kouh's PhD thesis and Kouh and Poggio, Neural Computation 2008.
There are subtle differences between the two. For example, a normalized
dot-product (i.e. a cosine operation) is mostly selective to the angle between
the input and prototype vectors, and grows with input magnitude (or is
independent of input magnitude if the additive constant in the denominator is
zero); whereas Gaussian tuning will return decreasing values if the input
magnitude 'overshoots' the prototype point. This might be useful if feedback
were implemented.

However, in this implementation the main reason for choosing the normalized
dot-product as the tuning operation is that it is extremely easy to implement:
the dot-product is simply a 3D-convolution (more precisely, cross-correlation)
between the inputs (stacking various prototypes of the input layers in the
depth dimension) and the prototype. The normalization denominator can also be
computed with cross-correlation, using a uniform filter. This 3D
cross-correlation is implemented either using Fourier transforms for S1 (which
is the faster option due to the presence of large filters and the non-sparse
prototypes), or by summing shifted copies of the inputs multiplied by the
prototype weights for other S layers, which is faster due to the sparseness of
S2/S3 prototypes (large proportion of non-existent weights within the overall
RF). Other options were tried (scipy.ndimage.filters.correlate,
scipy.signal.fftconvolve, Fourier transform for non-S1 groups), but these
choices seemed to provide the best performance.

Happy Hmaxing!
