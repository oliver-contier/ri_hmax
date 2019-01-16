#!/usr/bin/python

"""
This script defines generic functions for calculating the efficiency of a given design matrix and contrasts.
When used in an iteration, this can be used to maximize design efficiency for a given experiment.
However, except for compute_efficiency() and compute_vif(), they are tailored to my specific experiment.

Execute this script to run an iteration through a ton of designs for the RIRSA experiment
and keep only the most efficient ones. The results are stored in a json file.
"""

import json
from copy import deepcopy
from os.path import join as pjoin

import numpy as np
from mvpa2.misc.data_generators import simple_hrf_dataset

from fmri_sequences import make_rsa_run_sequence, add_catches, add_itis
from misc import getstims_aloiselection, mock_exp_info


def simulate_glm_run(percept_dicts, intact_dicts, exp_info,
                     minjit=0.8,
                     maxjit=1.5,
                     avjit=1.0,
                     reps_per_run=1,
                     catches=20,
                     assign_training=True,
                     remove_irrelevant_keys=(
                             'Alter', 'Geschlecht', 'RT', 'Rechtshaendig', 'Sitzung', 'SubjectID', 'accuracy', 'date',
                             'global_onset_time', 'responses', 'rotation', 'ran', 'object_id', 'object_name',
                             'trial_num', 'file_path', 'exp_name', 'first_trigger')  # , 'last_dummy_trigger')
                     ):
    """
    Create a simulated functional run of the RIRSA experiment to be used in the efficiency sampling.

    This run contains both intact object images and ri percepts, one full repetition of each. It also contains catch
    trials and everything. The order of events is randomized (except for the constraints on catch trials, which are
    not allowed to be in the first or last position or right after one another). Half of both types of stimuli are
    assigned either 'trained' or 'untrained'.
    """
    # get sequence for intact and ri seperately (without catch trials),
    # by using one of my functions
    percept_sequence = make_rsa_run_sequence(percept_dicts, exp_info, reps_per_run=reps_per_run, with_catches=False,
                                             with_itis=False, miniti=minjit, maxiti=maxjit, aviti=avjit)
    percept_sequence = percept_sequence[0]
    intact_sequence = make_rsa_run_sequence(intact_dicts, exp_info, reps_per_run=1, with_catches=False,
                                            with_itis=False, miniti=minjit, maxiti=maxjit, aviti=avjit)
    intact_sequence = intact_sequence[0]

    # assign 'trained' and 'untrained' markers to half of each intact and ri stimuli
    if assign_training:
        for perc_stim, int_stim in zip(percept_sequence[:len(percept_sequence) // 2],
                                       intact_sequence[:len(intact_sequence) // 2]):
            perc_stim['training'] = 'trained'
            int_stim['training'] = 'trained'
        for perc_stim, int_stim in zip(percept_sequence[len(percept_sequence) // 2:],
                                       intact_sequence[len(intact_sequence) // 2:]):
            perc_stim['training'] = 'untrained'
            int_stim['training'] = 'untrained'

    # merge
    # TODO: here is where I could have constraints on my sequence
    # (e.g. not more than 5 stims per condition in a row, or similar)
    full_seq = intact_sequence + percept_sequence

    # add catches and shuffle
    full_seq = add_catches(full_seq, num_catches=catches, shuffle_inlist=True)

    # add_itis to whole sequence
    full_seq = add_itis(full_seq, min_iti=minjit, max_iti=maxjit, av_iti=avjit)

    # remove sequence info that has no meaning for the design simulation
    if remove_irrelevant_keys:
        for stim in full_seq:
            for remkey in remove_irrelevant_keys:
                stim.pop(remkey)

    return full_seq


def add_ons_dur_inten(stimsequence,
                      stimdur=.8,
                      fixdur=.2,
                      intensity=1):
    """
    Add onset, duration, and intensity to stimulus sequence. All onsets will be realtive to the first trial in the
    sequence. The trials must have a key called 'iti'.
    """

    # onsets
    for idx in range(len(stimsequence)):
        if idx == 0:
            # all onsets are relative to first trial (with onset 0) for purpose of compute_efficiency estimation
            stimsequence[idx]['onset'] = 0
        else:
            stimsequence[idx]['onset'] = stimsequence[idx - 1]['onset'] + fixdur + stimdur + stimsequence[idx - 1][
                'iti']
        # durations + intensities
        stimsequence[idx]['duration'] = stimdur
        stimsequence[idx]['intensity'] = intensity

    return stimsequence


def extract_onsets(stim_sequence):
    """
    Take a stimulus sequence and return seperate lists of onsets for trained and untrained for both ri and intact
    object stimuli. Results are returned in a dict.
    """
    # initiate list of regressor dicts to save the onsets.
    regressors = [
        {'regname': 'intact_trained', 'onsets': []},
        {'regname': 'intact_untrained', 'onsets': []},
        {'regname': 'ri_percept_trained', 'onsets': []},
        {'regname': 'ri_percept_untrained', 'onsets': []},
        {'regname': 'catch', 'onsets': []}
    ]

    # set regressor values by going through the stim sequence
    for stim in stim_sequence:

        if stim['trial_type'] == 'catch':
            regressors[4]['onsets'].append(stim['onset'])
            continue
        else:
            if stim['vision'] == 'intact' and stim['training'] == 'trained':
                regressors[0]['onsets'].append(stim['onset'])
            elif stim['vision'] == 'intact' and stim['training'] == 'untrained':
                regressors[1]['onsets'].append(stim['onset'])
            elif stim['vision'] == 'ri_percept' and stim['training'] == 'trained':
                regressors[2]['onsets'].append(stim['onset'])
            elif stim['vision'] == 'ri_percept' and stim['training'] == 'untrained':
                regressors[3]['onsets'].append(stim['onset'])
            else:
                raise IOError('could not assess trial with index %i' % stim_sequence.index(stim))

    return regressors


def construct_design_matrix(onset_dicts):
    """
    Take dict of onsets for the different trial types and create a design matrix, including intercept, from it.
    """

    # convolve onsets with hrf to get regressors
    regressors_conv = []
    for onset_dict in onset_dicts:
        convolved_ds = simple_hrf_dataset(events=onset_dict['onsets'], tr=2, tres=1,
                                          baseline=0, signal_level=1, noise_level=0)
        convolved_reg = convolved_ds.sa['design'].value[:, 0]
        # pymvpa scales effect sizes to 2. We want them to be 1
        convolved_reg_scaled = convolved_reg / 2
        regressors_conv.append(convolved_reg_scaled)

    # padd regressors to same length
    # determine maximum length
    maxlen = 0
    for onset_dict in regressors_conv:
        if len(onset_dict) >= maxlen:
            maxlen = len(onset_dict)

    # pad shorter regressors accordingly
    for onset_dict in regressors_conv:
        if len(onset_dict) < maxlen:
            regressors_conv[regressors_conv.index(onset_dict)] = np.pad(onset_dict,
                                                                        (0, maxlen - len(onset_dict)), 'edge')

    # construct intercept vector and add to first position
    intercept = np.ones(len(regressors_conv[0]))
    design_matrix = np.vstack((intercept, regressors_conv))

    # get dimensions right (rows should be samples, columns should be regressors)
    design_matrix = design_matrix.transpose()

    return design_matrix


def prebuilt_contrasts():
    """
    This is a fixed set of contrast that matches my design matrices in the RIRSA experiment.
    """
    # intact > ri_percept
    cvec1 = np.array([0, 1, 1, -1, -1, 0])
    # intact < ri_percept
    cvec2 = np.array([0, -1, -1, 1, 1, 0])
    # ri_trained > ri_untrained
    cvec3 = np.array([0, 0, 0, 1, -1, 0])
    # ri_trained < ri_untrained
    cvec4 = np.array([0, 0, 0, -1, 1, 0])
    # stack arrays into contrast matrix
    cmat = np.vstack((cvec1, cvec2, cvec3, cvec4))
    return cmat


def compute_efficiency(design_matrix, contrast_matrix):
    """
    Compute design efficiency given a design matrix and a contrast matrix

    TODO: make this flexible for single contrast vectors as well
    """
    eff = 1 / np.trace(
        contrast_matrix.dot(np.linalg.inv(design_matrix.T.dot(design_matrix))).dot(contrast_matrix.T))
    return eff


def compute_vif(design_matrix):
    """
    Compute variance inflation factors (vif) for a given design matrix.
    Returns a flat array with one vif for each regressor in the design matrix.
    """
    # omit intercept
    design_matrix_omitted = design_matrix[:, 1:]
    # calculate vif
    vif = np.diagonal(np.linalg.inv(np.corrcoef(design_matrix_omitted, rowvar=False)))
    return vif


# def iterate_over_designs_deprecated(niters=10,
#                                     stim_dur=.8,
#                                     maxiti=1.5,
#                                     miniti=0.8,
#                                     aviti=1.0,
#                                     keepbest=3,
#                                     stimbasedir='/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/',
#                                     savesequences=True,
#                                     saveasjson='./results_design_opt.json'):
#     """
#     Use 'iterate_over_designs()' instead, which is computationally more efficient
#     """
#
#     # get stimulus dicts
#     perc_dir, prep_dir = pjoin(stimbasedir, 'percepts'), pjoin(stimbasedir, 'preprocessed')
#     percept_dicts, intact_dicts = getstims_aloiselection(percepts_dir=perc_dir, preprocessed_dir=prep_dir)
#     # make dummy experiment info
#     exp_info = mock_exp_info()
#     # make contrasts
#     cmat = prebuilt_contrasts()
#
#     # initialize results arrays
#     efficiencies, vifs, sequences = [], [], []
#
#     for i in range(niters):
#         # simulate a fake run
#         stim_seq = simulate_glm_run(percept_dicts, intact_dicts, exp_info,
#                                     maxjit=maxiti, minjit=miniti, avjit=aviti)
#         stim_seq = add_ons_dur_inten(stim_seq, stimdur=stim_dur)
#         # extract onsets and make design matrix
#         onsetdicts = extract_onsets(stim_seq)
#         designmatrix = construct_design_matrix(onsetdicts)
#
#         # calculate parameters and append to results
#         efficiencies.append(compute_efficiency(contrast_matrix=cmat, design_matrix=designmatrix))
#         vifs.append(compute_vif(designmatrix))
#
#         if savesequences:
#             sequences.append(stim_seq)
#
#     # only keep N most efficient designs
#     effs_arr = np.array(efficiencies)
#     best_ids = effs_arr.argsort()[-keepbest:]
#     best_effs = effs_arr[best_ids]
#     seqs_arr = np.array(sequences)
#     best_seqs = seqs_arr[best_ids]
#     vifs_arr = np.array(vifs)
#     best_vifs = vifs_arr[best_ids]
#
#     # object to store the results in
#     # (note: json can't save np.arrays, so we have to convert to lists ... ).
#     results = {
#         'efficiencies': best_effs.tolist(),
#         'vifs': best_vifs.tolist(),
#         'maxiti': maxiti, 'miniti': miniti, 'aviti': aviti, 'niters': niters
#     }
#     # only add sequence to final result array if desired.
#     if savesequences:
#         results['sequences'] = best_seqs.tolist()
#
#     # save json file
#     if saveasjson:
#         with open(saveasjson, 'w') as f:
#             json.dump(results, f)
#
#     return results


def iterate_over_designs(niters=10,
                         stim_dur=1.1,
                         maxiti=1.5,
                         miniti=0.8,
                         aviti=1.0,
                         keepbest=3,
                         stimbasedir='/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/',
                         savesequences=True,
                         saveasjson='./results_design_opt.json'):
    """
    Simulate a multitude of stimulus sequences and compute efficiency parameters. The results, along with the actual
    sequences, will be stored in a dict, with seperate keys for sequences, efficiencies, etc. Only the best N
    as measured by design efficiency will be kept and stored in a json file.
    """

    # get stimulus dicts
    perc_dir, prep_dir = pjoin(stimbasedir, 'percepts'), pjoin(stimbasedir, 'preprocessed')
    percept_dicts, intact_dicts = getstims_aloiselection(percepts_dir=perc_dir, preprocessed_dir=prep_dir)
    # make dummy experiment info
    exp_info = mock_exp_info()
    # make contrasts
    cmat = prebuilt_contrasts()

    # initialize results arrays
    efficiencies, vifs, sequences = [], [], []

    for i in range(niters):
        # simulate a fake run
        stim_seq = simulate_glm_run(percept_dicts, intact_dicts, exp_info,
                                    maxjit=maxiti, minjit=miniti, avjit=aviti)
        stim_seq = add_ons_dur_inten(stim_seq, stimdur=stim_dur)

        # extract onsets and make design matrix
        onsetdicts = extract_onsets(stim_seq)
        designmatrix = construct_design_matrix(onsetdicts)

        # compute efficiency and vif
        efficiency = compute_efficiency(contrast_matrix=cmat, design_matrix=designmatrix)
        vif = compute_vif(designmatrix)

        # while there are fewer designs simulated than we want to keep, just store the results
        if len(efficiencies) < keepbest:
            efficiencies.append(efficiency)
            vifs.append(vif.tolist())
            sequences.append(stim_seq.tolist())
        # else, only store if the new efficiency improves over the old ones
        else:
            # copy efficiencies, so we don't accidentally mess up the sorting
            efficiencies_copy = deepcopy(efficiencies)
            # find worst efficiency so far
            efficiencies_copy.sort()
            worst_eff = efficiencies_copy[0]
            if efficiency > worst_eff:
                # delete worst efficiency from all list by index
                worst_idx = efficiencies.index(worst_eff)
                for result_list in [efficiencies, vifs, sequences]:
                    del result_list[worst_idx]
                # and append the better results
                efficiencies.append(efficiency)
                vifs.append(vif.tolist())
                sequences.append(stim_seq.tolist())

    # store all results in dict
    results = {'efficiencies': efficiencies, 'vifs': vifs,
               'maxiti': maxiti, 'miniti': miniti, 'aviti': aviti, 'niters': niters}
    # only add sequence to final result array if desired.
    if savesequences:
        results['sequences'] = sequences

    # save json file
    if saveasjson:
        with open(saveasjson, 'w') as f:
            json.dump(results, f)

    return results


if __name__ == '__main__':
    sim_results = iterate_over_designs(niters=50000, keepbest=400, stim_dur=1.1, stimbasedir='./Stimuli')
