#!/usr/bin/env python

import numpy as np
from numpy import exp
from scipy.stats import pearsonr


# TODO: Function to create pairwise distance matrix between RI patterns, given pattern_df.
# TODO: Kullbach-Leibler divergence between categories in hmax space.


def compute_s(pattern1, pattern2):
    """
    Compute similarity measure between two response patterns corresponding to two stimuli.
    First, distance metric is computed and then transformed to similarity metric.
    """
    distance = (1 - pearsonr(pattern1, pattern2)[0]) / 2
    similarity = exp(-distance)
    return similarity


def compute_typ(similarities, average=False):
    """
    Take a list of pairwise similarities and compute typicality from it.
    If the object categories you're interested in have different numbers of exemplars, you should turn average=True.
    Otherwise, typicality will simply be the sum over all pairwise similarities as in Davis & Poldrack (2016).
    """
    typ = np.sum(similarities)
    if average:
        typ = typ / len(similarities)
    return typ


def add_typicalities(df, avrg=False):
    """
    Take a pandas data frame and automatically compute conserved, intact, and RI typicality.
    df should containing rows for the stimulus name (e.g. "apple_1"), category (e.g. "apple"),
    ri_pattern and intact_pattern (arrays or lists containing hmax cell activations, fMRI data, etc.).

    :param df: Data Frame. pattern df created with hmaxout2df function.
    :param avrg: bool. If true, take the average instead of summing over all pairwise distances during computation of
    typicality measures. Use this when the number of stimuli varies between categories.
    :return: df. Data Frame. pattern df with added newfound, intact, and conserved tyicality.
    """

    # iterate through exemplars
    for row in df.exemplar:
        # get category name and target pattern
        catname = df[df.exemplar == row].category.values[0]

        # get within-category stimuli
        cat_df = df[(df.category == catname) &
                    (df.exemplar != row)]

        # compute ri typicality and intact typicality
        for colname, pattern_type in zip(['ri_typ', 'intact_typ'],
                                         ['ri_pattern', 'intact_pattern']):
            target_pattern = df[df.exemplar == row][pattern_type]
            assert len(target_pattern) == len(df.ri_pattern.values[0])  # check whether all pattern lengths are equal
            similarities = [compute_s(target_pattern, cat_pattern)
                            for cat_pattern in cat_df[pattern_type].values]
            df[df.stimulus == row][colname] = compute_typ(similarities, average=avrg)

        # compute conserved typicality
        target_ri_pattern = df[df.exemplar == row].ri_pattern
        conserved_similarities = [compute_s(target_ri_pattern, cat_intact_pattern)
                                  for cat_intact_pattern in cat_df.intact_patterns.values]
        df[df.stimulus == row]['conserved_typ'] = compute_typ(conserved_similarities, average=avrg)

    return df
