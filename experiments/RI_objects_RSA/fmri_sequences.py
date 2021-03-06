#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Functions needed for building and handling stimulus sequences in the scanner
"""

import copy
import random
from os.path import join as pjoin

import numpy as np
from numpy.random import exponential

from misc import checkconsec, checkfirstlast, assertplus2, add_expinfo, getstims_aloiselection

def add_empty_responses(stimsequence,
                        add_global_onset=True,
                        add_firsttrig=True,
                        add_trial_num=True):
    """
    Add empty dummy information for the to-be-captured responses to each stimulus dict in sequence. These are:
    Rt, accuracy, keys, trial_num, and ran. This will allow all trials with their information to be written in the
    logg-file even if they haven't run yet.

    To use this function on pre-generated sequences (from design optimization), that already have onsets and trial
    numbers, these keys may optionally not be added
    """
    for trial_num, stimdict in enumerate(stimsequence):
        if add_global_onset:
            stimdict['global_onset_time'] = None  # time relative to first trigger
        if add_firsttrig:
            stimdict['first_trigger'] = None  # time from start of this script to the first trigger
        stimdict['RT'] = None
        stimdict['accuracy'] = None
        stimdict['responses'] = None  # keys pressed durint a trial
        if add_trial_num:
            stimdict['trial_num'] = trial_num + 1
        stimdict['ran'] = False  # was the trial presented
    return stimsequence


def add_catches(stimlist,
                num_catches=10,
                shuffle_inlist=True):
    """
    Add catch trials for a 1-back taks to a given stimulus sequence by repeating randomly chosen trials.
    Catch trials are not allowed To occur in first or last position of the sequence, nor can two catch trials follow
    one another. Also adds the "trial_type" key to each stimulus dict with values "normal" or "catch".
    """

    # assert that we didn't specify too many catch trials given our constraints
    assertplus2(stimlist, range(num_catches))
    # shuffle if desired
    if shuffle_inlist:
        random.shuffle(stimlist)
    # initial key-value indicating if this is a catch or normal trial
    for stim in stimlist:
        stim['trial_type'] = 'normal'

    # make list of random, non-consecutive positions for catch trials
    # with added constraint that first and last trials mustn't be catch trials
    consec_bool, firstlast_bool = True, True
    insert_positions = None
    while consec_bool or firstlast_bool:
        insert_positions = np.array(sorted(random.sample(range(len(stimlist)), num_catches)))
        consec_bool, firstlast_bool = checkconsec(insert_positions), checkfirstlast(insert_positions, stimlist)

    # make stimlist an array to get numpy goodness
    stimlist = np.array(stimlist)

    # copy to-be-catch stimuli so we don't have pointer problems
    catchstims = copy.deepcopy(stimlist[insert_positions])

    # insert their copies at the positions before
    stimlist_ins = np.insert(stimlist, insert_positions, catchstims)

    # mark catch trials trial_type whenever there are two identical consecutive trials
    assert_counter = 0
    for idx in range(len(stimlist_ins)):
        if idx == 0:
            continue
        elif stimlist_ins[idx] == stimlist_ins[idx - 1]:
            stimlist_ins[idx]['trial_type'] = 'catch'
            assert_counter += 1
    assert assert_counter == num_catches

    # reassign trial number (because else they will still be copies)
    for idx in range(len(stimlist_ins)):
        stimlist_ins[idx]['trial_num'] = idx + 1

    return stimlist_ins


def sample_itis_shiftruncexpon(miniti=800.,
                               maxiti=1500.,
                               aviti=1000.,
                               ntrials=141):
    """
    Sample ITIs from truncated exponential distribution which is shifted by a minimum value and limited to a maximum.
    """
    distmax = maxiti + 1
    shifted = None
    while distmax > maxiti:
        lamb = aviti - miniti
        unshifted = exponential(scale=lamb, size=ntrials)
        shifted = unshifted + miniti
        distmax = np.max(shifted)
    return shifted


def add_itis(stim_sequence,
             min_iti,
             max_iti,
             av_iti,
             jitter='shiftruncexpon'):
    """
    Add jittered inter trial intervals to a stimulus sequence.
    """
    if not jitter == 'shiftruncexpon':
        raise IOError('only the jitter type shifted truncated exponential is supported for now')
    itis = sample_itis_shiftruncexpon(miniti=min_iti, maxiti=max_iti, aviti=av_iti, ntrials=len(stim_sequence))
    for stim, iti in zip(stim_sequence, itis):
        stim['iti'] = iti
    return stim_sequence


def make_rsa_run_sequence(stimdicts,
                          experiment_info,
                          reps_per_run=4,
                          with_catches=True,  # if False, don't add catch trials
                          ncatches=10,  # number of catch trials
                          with_itis=True,
                          miniti=.8,  # jitter args
                          maxiti=1.5,
                          aviti=1.):
    """
    Take stimulus dicts and create a list of lists, with each sublist representing the stimulus sequence of one block
    and the number of sublists corresponding to the number of blocks/repetitions in one functional run.

    Parameters
    ----------
    stimdicts : list
        each list entry represents one stimulus gathered with getstims_aloiselection
    experiment_info : dict
        additional experiment information gathered from the psychopy gui
    reps_per_run : int
        number of blocks in one functional run

    Returns
    -------
    run_sequences : list of lists
        Each sublists represents one block, and the sublist elements each represent a trial. The whole list contains
        all blocks of a given functinal run.
    """

    run_sequences = []
    for block in range(1, reps_per_run + 1):
        # for each block, create a seperate copy and add exp_info, empty responses, catches, jitter, and block number
        block_sequence = copy.deepcopy(stimdicts)
        block_sequence = add_expinfo(block_sequence, experiment_info)
        block_sequence = add_empty_responses(block_sequence)
        if with_catches:
            block_sequence = add_catches(block_sequence, num_catches=ncatches)
        if with_itis:
            block_sequence = add_itis(block_sequence, jitter='shiftruncexpon',
                                      min_iti=miniti, max_iti=maxiti, av_iti=aviti)
        for trial in block_sequence:
            trial['block'] = block
        run_sequences.append(block_sequence)

    return run_sequences


def read_trained_objects(behav_data_dir='./behav_data',
                         sub_id='p1'):
    """
    Get the set of trained objects from the behavioral results csv file
    for a given subject.
    """
    import pandas as pd
    fname = '%s/sub%s_behav.csv' % (behav_data_dir, sub_id)
    behav_df = pd.read_csv(fname)
    trained_obs = np.unique(behav_df.object_name)
    return trained_obs


def read_designopt_json(results_filepath='results_design_opt.json'):
    """
    Read json file that contains the results from the design optimation procedure

    NOTE: the best designs are at the end of the lists
    """
    import json
    with open(results_filepath, 'rb') as f:
        results = json.load(f)
    return results

def load_glm_run(sub_id,
                 nruns=3,
                 test=False,
                 behav_data_dir='./behav_data',
                 stim_dir='./Stimuli',
                 designopt_json='results_design_opt.json'):
    """
    From the efficiency optimized trial sequences, grab as many as we want there to be functional runs
    and bring them in shape for presentation with psychopy.

    --Notes--
    Each subject gets 3 of the glm optized functional runs.
    The last onset within each of these designs is at about 550 seconds (~9:10 minutes).
    sub_id looks like '01' for real subjects, and is 'p1' for testing purposes.
    subject 1 gets the best sequences, the next subject the next best, etc.
    (remember, best designs are at end of the array).
    """

    # get sub_int from sub_id
    if test:
        sub_int = 1
    else:
        sub_int = int(sub_id)

    # get designs for this subject
    designopt_results = read_designopt_json(results_filepath=designopt_json)
    if sub_int == 1:
        sub_sequences = designopt_results['sequences'][(-(sub_int * nruns)):]
    else:
        sub_sequences = designopt_results['sequences'][(-(sub_int * nruns)):(-(sub_int - 1) * nruns)]
    assert len(sub_sequences) == nruns

    """
    create seperate lists of dicts for ri and intact trained and untrained respectively
    """

    # get percept and intact dicts
    perc_dir = pjoin(stim_dir, 'percepts')
    prep_dir = pjoin(stim_dir, 'preprocessed')
    percept_dicts, intact_dicts = getstims_aloiselection(percepts_dir=perc_dir, preprocessed_dir=prep_dir)
    # get set of trained objects for this subject
    trained_obs = read_trained_objects(sub_id=sub_id, behav_data_dir=behav_data_dir)
    # initiate empty stimulus lists
    ri_trained, ri_untrained, intact_trained, intact_untrained = [], [], [], []

    # go through all percepts and add to trained vs. untrained list
    for perc in percept_dicts:
        if perc['object_name'] in trained_obs:
            ri_trained.append(perc)
        else:
            ri_untrained.append(perc)
    assert len(ri_trained) == 64
    assert len(ri_untrained) == 64
    # same for intact stimuli
    for intact in intact_dicts:
        if intact['object_name'] in trained_obs:
            intact_trained.append(intact)
        else:
            intact_untrained.append(intact)
    assert len(intact_trained) == 64
    assert len(intact_untrained) == 64

    # shuffle those lists
    for stimlist in [ri_trained, ri_untrained, intact_trained, intact_untrained]:
        random.shuffle(stimlist)

    """
    Go through the trials and add information of a stimulus
    that matches the training and vision
    """
    # go through the runs / sequences
    for sequence in sub_sequences:
        # indices
        ri_trained_i, ri_untrained_i, intact_trained_i, intact_untrained_i = 0, 0, 0, 0
        for design_trial in sequence:

            # add correct block number
            design_trial['block'] = sub_sequences.index(sequence) + 1

            # repeat previous trial if this is a catch
            if design_trial['trial_type'] == 'catch':
                assert sequence.index(design_trial) > 0
                # grab last trial
                stimdict = sequence[sequence.index(design_trial) - 1]
                # add the information to design sequence
                design_trial.update(stimdict)
                # mark as catch
                design_trial['trial_type'] = 'catch'

            # normal trials
            else:
                # trained ri
                if design_trial['training'] == 'trained' and design_trial['vision'] == 'ri_percept':
                    stimdict = ri_trained[ri_trained_i]
                    ri_trained_i += 1
                # untrained ri
                elif design_trial['training'] == 'untrained' and design_trial['vision'] == 'ri_percept':
                    stimdict = ri_untrained[ri_untrained_i]
                    ri_untrained_i += 1
                # trained intact
                elif design_trial['training'] == 'trained' and design_trial['vision'] == 'intact':
                    stimdict = intact_trained[intact_trained_i]
                    intact_trained_i += 1
                # untrained intact
                elif design_trial['training'] == 'untrained' and design_trial['vision'] == 'intact':
                    stimdict = intact_untrained[intact_untrained_i]
                    intact_untrained_i += 1

                # add the information to design sequence
                design_trial.update(stimdict)

        # check if we have actually gone through all the stimuli with our indices
        for idx in [ri_trained_i, ri_untrained_i, intact_trained_i, intact_untrained_i]:
            assert idx == len(percept_dicts) / 2

        # add responses, block info, etc. to this sequence
        sequence = add_empty_responses(sequence, add_global_onset=True, add_trial_num=True)

    return sub_sequences
