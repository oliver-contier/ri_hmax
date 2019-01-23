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
    # TODO: ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
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

    :param df: Data Frame
        pattern df created with hmaxout2df function.
    :param avrg: bool
        If true, take the average instead of summing over all pairwise distances during computation of
    typicality measures. Use this when the number of stimuli varies between categories.

    :return: df
        Data Frame. pattern df with added newfound, intact, and conserved tyicality.
    """

    # iterate through categories in this data frame
    for catname in np.unique(df.category.values):
        # create new data frame for this category
        cat_df = df[df.category == catname]
        # TODO: assert that each exemplar only occurs once for this category
        # iterate through exemplars of this category
        for exemplar_ in cat_df.exemplar.values:
            # find all other exemplars. returns a data frame
            other_exemplars = cat_df[cat_df.exemplar != exemplar_]

            # compute within-vision (ri to ri, and intact to intact) similarities
            for colname, pattern_type in zip(['ri_typicality', 'intact_typicality'],
                                             ['ri_pattern', 'intact_pattern']):
                similarities = [
                    compute_s(
                        cat_df[cat_df.exemplar == exemplar_][pattern_type].values[0],  # target pattern
                        other_pattern  # other exemplar's pattern
                    )
                    for other_pattern in other_exemplars[pattern_type].values.tolist()
                ]

                # compute typicality and add to data frame
                typicality = compute_typ(similarities, average=avrg)
                df.loc[(df['exemplar'] == exemplar_) & (df['category'] == catname),
                       colname] = typicality

            # compute conserved similarities and typicality
            conserved_similarities = [
                compute_s(
                    cat_df[cat_df.exemplar == exemplar_]['ri_pattern'].values[0],
                    other_pattern
                )
                for other_pattern in other_exemplars['intact_pattern'].values.tolist()
            ]
            conserved_typicality = compute_typ(conserved_similarities, average=avrg)
            # append to df
            df.loc[(df['exemplar'] == exemplar_) & (df['category'] == catname),
                   'conserved_typicality'] = conserved_typicality

    return df
