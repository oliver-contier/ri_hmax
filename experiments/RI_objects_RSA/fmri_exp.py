#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Script for stimulus presentation in the scanner.
# TODO: describe script usage (when finished)
"""

import copy
import os
import random
from collections import OrderedDict
from os.path import join as pjoin

import numpy as np
from numpy.random import exponential
from psychopy import core, visual, event

from general import getstims_aloiselection, list_of_dictlists_2csv, add_expinfo, draw_gui, pick_monitor


def showinstr(instring='Weiter mit der Leertaste'):
    """
    Show instructions and wait for key press (space bar).

    Parameters
    ----------
    instring : str
        String you want to be presented as instructions.

    Returns
    -------
    None
    """

    # create and draw window, flip screen.
    win = visual.Window(color='black', units='pix', fullscr=True)  # size=(1680, 1050)
    text = visual.TextStim(win, text=instring, color='white', height=20)
    text.draw()
    win.flip()

    # await keyboard input and close screen.
    keys = event.waitKeys(keyList=['space', 'escape'])
    if 'escape' in keys:
        win.close()
    else:
        print 'End of instructions'
        win.close()


def checkconsec(integerlist):
    """
    Helper function.
    Check whether a list of integers contains consecutive numbers. Returns True or False.
    """
    # make an ordered copy of original input list
    ordered = [i for i in integerlist]
    ordered.sort()
    # check for consecutive list elements
    consec = False
    for element in ordered[1:]:
        if element == ordered[ordered.index(element) - 1] + 1:
            consec = True
    return consec


def checkfirstlast(indiceslist,
                   targetlist):
    """
    Check if list of indices contains index for first or last element of a target list
    (i.e. 0 or len(elementlist)-1 )
    """
    # check constraint
    firstlast = False
    lastidx = len(targetlist) - 1
    if 0 in indiceslist or lastidx in indiceslist:
        firstlast = True
    return firstlast


def assertplus2(list1, list2):
    """
    Assert if list1 has at least two more elements than list2
    """
    if len(list1) < len(list2) + 2:
        raise IOError('Too many catch trials for stimulus sequence, given constraint checkfirstlast.\n'
                      'length of stimulus list : %s\n'
                      'number of desired catch trials : %s'
                      % (str(len(list1)), str(len(list2))))
    return None


def add_empty_responses(stimsequence):
    """
    Add empty dummy information for the to-be-captured responses to each stimulus dict in sequence. These are:
    Rt, accuracy, keys, trial_num, and ran. This will allow all trials with their information to be written in the
    logg-file even if they haven't run yet.
    """
    for trial_num, stimdict in enumerate(stimsequence):
        stimdict['global_onset_time'] = None
        stimdict['RT'] = None
        stimdict['accuracy'] = None
        stimdict['keys'] = None
        stimdict['trial_num'] = trial_num
        stimdict['ran'] = False
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
    # make copy of original list
    # shuffle if desired
    if shuffle_inlist:
        random.shuffle(stimlist)
    # add key-value indicating if this is a catch or normal trial
    for stim in stimlist:
        stim['trial_type'] = 'normal'

    # make list of random, non-consecutive positions for catch trials
    # with constraint that first and last trials mustn't be catch trials
    consec_bool, firstlast_bool = True, True
    catchpositions = None
    while consec_bool or firstlast_bool:
        catchpositions = random.sample(range(len(stimlist)), num_catches)
        consec_bool, firstlast_bool = checkconsec(catchpositions), checkfirstlast(catchpositions, stimlist)

    # choose items in new_stimlist (i.e. percept_dict) that should be followed by catch trials
    catchstims = [stimlist[pos] for pos in catchpositions]

    # insert catchstims into list at appropriate index
    # and mark them with 'catch'
    for catchstim in catchstims:
        stimlist.insert(stimlist.index(catchstim) + 1, catchstim)
        stimlist[stimlist.index(catchstim) + 1]['trial_type'] = 'catch'

    # make new list with copy of each original dict, else multiple entries will point to same object in memory
    stimlist_copy = [copy.copy(stimdict) for stimdict in stimlist]

    # flip trial_type of the stim right before catch trial back to 'normal'
    for idx, stim in enumerate(stimlist_copy[:-1]):
        if stimlist_copy[idx + 1]['trial_type'] == 'catch':
            stim['trial_type'] = 'normal'

    return stimlist_copy


def sample_itis_shiftruncexpon(miniti=800.,
                               maxiti=1500.,
                               aviti=1000.,
                               ntrials=141):
    """
    Sample ITIs from truncated exponential distribution which is shifted by a minimum value.
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
             min_iti=.8,
             max_iti=1.5,
             av_iti=1.,
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


def make_run_seq(stimdicts,
                 experiment_info,
                 blocksperrun=4):  # maybe add args for jitter timing
    """
    Take stimulus dicts and create a list of lists, with each sublist representing the stimulus sequence of one block
    and the number of sublists corresponding to the number of blocks/repetitions in one functional run.

    Parameters
    ----------
    stimdicts : list
        each list entry represents one stimulus gathered with getstims_aloiselection
    experiment_info : dict
        additional experiment information gathered from the psychopy gui
    blocksperrun : int
        number of blocks in one functional run

    Returns
    -------
    run_sequences : list of lists
        Each sublists represents one block, and the sublist elements each represent a trial. The whole list contains
        all blocks of a given functinal run.
    """

    run_sequences = []
    for block in range(1, blocksperrun + 1):
        # for each block, create a seperate copy and add exp_info, empty responses, catches, jitter, and block number
        block_sequence = copy.deepcopy(stimdicts)
        block_sequence = add_expinfo(block_sequence, experiment_info)
        block_sequence = add_empty_responses(block_sequence)
        block_sequence = add_catches(block_sequence)
        block_sequence = add_itis(block_sequence, jitter='shiftruncexpon')
        for trial in block_sequence:
            trial['block'] = block
        run_sequences.append(block_sequence)

    return run_sequences


def present_run(run_sequence,
                output_csv,
                response_key='space',
                escape_key='escape',
                trigger_key='t',
                stimsize=15,
                fixdur=.500,
                stimdur=1.,
                skip_volumes=4,
                monitorname='skyra_projector'):
    """

    """
    # TODO: docstring
    # TODO: get monitor specifications from scanner (resolution, width, viewing distance, etc.)
    # TODO: use countdown timing (more precise)
    # TODO: transform presentation times into multiples of framerate, depends on monitor (but probably 60 Hz).

    # Initiate  windows, stimuli, and alike
    mon, window_ = pick_monitor(monitorname)
    event.Mouse(visible=False, win=window_)
    fixation = visual.ShapeStim(window_, size=1, lineWidth=5, closeShape=False, lineColor="white",
                                vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)))
    blank = visual.ShapeStim(window_, size=0, lineWidth=0, lineColor='black')
    stim = visual.ImageStim(window_, size=stimsize)
    escape_bool = False

    # clocks
    fix_rt = core.Clock()
    stim_rt = core.Clock()
    blank_rt = core.Clock()
    global_onset_time = core.Clock()
    firsttrig_time = core.Clock()
    skipvol_time = core.Clock()

    """
    Scanner warm up
    """

    # Wait for first scanner pulse
    firsttrig_instr = visual.TextStim(window_, text='waiting for first scanner pulse', color='white', height=2)
    firsttrig_instr.draw()
    window_.flip()
    firsttrig = event.waitKeys(keyList=[trigger_key], timeStamped=firsttrig_time)

    # do nothing during first few scans, which will be discarded before analysis
    global_onset_time.reset()
    skipvol_instr = visual.TextStim(window_, text='dummy scans', color='white', height=2)
    skipvol_instr.draw()
    window_.flip()
    for i in range(skip_volumes-1):
        dummy_keys = event.waitKeys(keyList=[trigger_key], timeStamped=skipvol_time)

    """
    Start task
    """

    # block loop
    for stim_sequence in run_sequence:

        if escape_bool:
            break

        # trial loop
        for trial in stim_sequence:

            if escape_bool:
                break

            # wait for keyboard input, time stamp with clock stim_rt
            responses = event.getKeys(keyList=[response_key, escape_key], timeStamped=stim_rt)

            # show fixation
            fix_rt.reset()
            while fix_rt.getTime() < fixdur:
                fixation.draw()
                window_.flip()

            # show stimulus
            stim.setImage(trial['file_path'])
            trial['global_onset_time'] = global_onset_time.getTime()
            stim_rt.reset()
            while stim_rt.getTime() < stimdur:
                stim.draw()
                window_.flip()

            # response evaluation
            trial['responses'] = responses
            if responses:
                trial['RT'] = responses[0][1]
                if trial['trial_type'] == 'normal':
                    trial['accuracy'] = 0
                elif trial['trial_type'] == 'catch':
                    trial['accuracy'] = 1
            else:
                if trial['trial_type'] == 'normal':
                    trial['accuracy'] = 1
                elif trial['trial_type'] == 'catch':
                    trial['accuracy'] = 0

            # show jittered blank
            blank_rt.reset()
            while blank_rt.getTime() < trial['iti']:
                blank.draw()
                window_.flip()

            # exit loop if escape key was pressed
            if responses and escape_key in responses[0]:
                escape_bool = True

            # tag this trial as presented
            trial['ran'] = True

    # add additional global info to trial dicts
    for blockseq in run_sequence:
        for trial in blockseq:
            trial['firsttrig_time'] = firsttrig[0][1]

    # write csv with output after trial loop has ended
    list_of_dictlists_2csv(run_sequence, output_csv)

    # end presentation
    window_.close()
    core.quit()

    return None


def run_first_session(stimbasedir,
                      outcsvdir,
                      nruns=4,
                      blocksprun=4,
                      testing=False,
                      mon_name='skyra_projector'):
    # create output directory
    if not os.path.exists(outcsvdir):
        os.makedirs(outcsvdir)

    # get stim sequence
    perc_dir = pjoin(stimbasedir, 'percepts')
    prep_dir = pjoin(stimbasedir, 'preprocessed')
    percept_dicts, intact_dicts = getstims_aloiselection(percepts_dir=perc_dir, preprocessed_dir=prep_dir)

    # draw gui to get exp_info
    if testing:
        exp_info = OrderedDict({'Alter': ' 1', 'Geschlecht': 'weiblich', 'Rechtshaendig': True, 'Sitzung': '1',
                                'SubjectID': '1', 'date': u'2018_Nov_06_1408', 'exp_name': 'RI_RSA'})
    else:
        exp_info = draw_gui(exp_name='RI_RSA')

    # TODO: instruction windows

    for run in range(1, nruns + 1):
        # make sequence for one run
        run_seq = make_run_seq(percept_dicts, exp_info, blocksperrun=blocksprun)
        # create csv file name (full path)
        csv_fname = pjoin(outcsvdir,
                          'sub%s_session%s_run%i_fmri.csv' % (exp_info['SubjectID'], exp_info['Sitzung'], run))
        # present one functional run
        present_run(run_seq, output_csv=csv_fname, monitorname=mon_name)

    return None


if __name__ == '__main__':
    stimdir = '/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/'
    outdir = os.path.dirname(os.path.realpath(__file__))

    run_first_session(stimbasedir=stimdir, outcsvdir=outdir, mon_name='samsung_office', testing=True)  # , testing=True)
