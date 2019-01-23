#!/usr/bin/env python

"""
Execute this python script to ...
- read all the hmax outputs for the aloi images (ri and intact) into a pandas data frame
- compute and add different typicalities
- save the resulting data frame as a pickle file
"""

if __name__ == "__main__":
    from aloi_handler import aloi_hmaxout2df_pickle
    hmaxoutdir = "/home/contier/ri_hmax/workdir/aloi/hmaxout"
    pickle_outfile = "/home/contier/ri_hmax/workdir/aloi/hmax_df.pickle"
    aloi_hmaxout2df_pickle(hmaxoutdir=hmaxoutdir, pickle_outfile=pickle_outfile)
