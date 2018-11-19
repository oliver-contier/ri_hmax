#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
hand-coded script for stimulus presentation in the scanner.
Include both first and second session and make adaptable by input GUI.
"""

import copy
import csv
import glob
import os
import random
from collections import OrderedDict
from os.path import join as pjoin

import numpy as np
from numpy.random import exponential
from psychopy import gui, core, data, visual, event


def show_gui(exp_name='retina_rep'):  # out_dir='./data',
    """
    Get session info from subject via a GUI.

    Parameters
    ----------
    out_dir : str
        path to folder where data is to be stored
    exp_name : str
        Name of the experiment, will be stored in exp_info

    Returns
    -------
    exp_info : dict
        containing subject ID, gender, age, etc.
    outfile : str
        full path to the output data file
    session : int
        is this fmri-session 1 or 2?
    """

    # if not os.path.exists(out_dir):
    #     os.makedirs(out_dir)

    # initiate dict with information collected from GUI input
    exp_info = {'SubjectID': '',
                'Gechlecht': ('maennlich', 'weiblich'),
                'Alter': ' ',
                'Rechtshaendig': True,
                'Sitzung': (1, 2)}

    # draw gui
    dlg = gui.DlgFromDict(dictionary=exp_info, title=exp_name)

    # quit gui if user clicks 'cancel'
    if not dlg.OK:
        core.quit()

    # add additional info to exp_info which doesn't come from GUI input
    exp_info = OrderedDict(exp_info)
    exp_info['exp_name'] = exp_name
    exp_info['date'] = data.getDateStr()

    # # output file path
    # outfile = pjoin(out_dir, exp_info['SubjectID'] + '_' + exp_info['date'] + '_sitzung_' + str(exp_info['Sitzung']))

    return exp_info


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


def get_stims_aloi_selection(percepts_dir='../Stimuli/percepts',
                             preprocessed_dir='../Stimuli/preprocessed'):
    """
    Create list of dicts containing information about all experimental stimuli, like their
    vision type ('ri_percept' vs. 'intact'), rotation, object_ID and file_path.

    Parameters
    ----------
    percepts_dir : str
        Path to directory with RI percept images (should be .png).
    preprocessed_dir : str
        Path to directory with intact object images (which were also preprocessed in my case).

    Returns
    -------
    percept_dicts : list of dicts
        Each dict stands for one RI percept stimulus, containing key-value pairs for vision, rotation, object_ID,
        and file path.
    intact_dicts : list of dicts
        Same as percept_dicts but for intact object stimuli.
    """
    #  check if input directory exists
    for directory in [percepts_dir, preprocessed_dir]:
        if not os.path.exists(directory):
            raise IOError('Could not find stimulus input directory : %s' % directory)

    # We want a list of dicts.
    # Each dict should have key-values for: Object number, rotation, vision
    percept_fpaths = glob.glob(percepts_dir + '/*.png')
    intact_fpaths = glob.glob(preprocessed_dir + '/*.png')

    # collect info from percept file names
    percept_dicts = []
    for percept_fpath in percept_fpaths:
        # vision1 and vision2 are not actually used for the dict
        object_ID, rotation, vision1, vision2 = tuple(percept_fpath.split('/')[-1].split('.')[0].split('_'))
        percept_dict = OrderedDict({'file_path': percept_fpath,
                                    'object_ID': object_ID,
                                    'rotation': int(rotation.replace('r', '')),
                                    'vision': 'ri_percept'})
        percept_dicts.append(percept_dict)

    # collect info from intact (prepped) object file names
    intact_dicts = []
    for intact_fpath in intact_fpaths:
        object_ID, rotation, vision = tuple(intact_fpath.split('/')[-1].split('.')[0].split('_'))
        intact_dict = OrderedDict({'file_path': intact_fpath,
                                   'object_ID': object_ID,
                                   'rotation': int(rotation.replace('r', '')),
                                   'vision': 'intact'})
        intact_dicts.append(intact_dict)

    return percept_dicts, intact_dicts


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


def add_expinfo_stimsequence(stimsequence, exp_info):
    """
    Add key-value pairs in exp_info to list of stimdicts defined in stim_sequence so it will be
    captured in our logg files.
    """
    for stimdict in stimsequence:
        stimdict.update(exp_info)
    return stimsequence


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


def dictlist2csv(dictlist, csv_fname):
    """
    Write a list of dictionaries to a csv file. In our case, this function is used to write the logg-file after all
    trials have run or experimenter exits via escape.
    This will only work if all dicts have the same keys.
    """
    # assert if all keys are the same
    for stimdict in dictlist[1:]:
        if not set(stimdict.keys()) == set(dictlist[0].keys()):
            raise IOError('not all dicts in dictlist have the same keys.')
    # write csv
    header_keys = dictlist[0].keys()
    with open(csv_fname, 'wb') as f:
        dict_writer = csv.DictWriter(f, header_keys)
        dict_writer.writeheader()
        dict_writer.writerows(dictlist)
    return None


def list_of_dictlists_2csv(dictlistslist, csv_fname):
    """
    take a list of lists, each containing dicts with equivalent keys and write their contents into a csv file.
    """
    header_keys = dictlistslist[0][0].keys()
    with open(csv_fname, 'wb') as f:
        dict_writer = csv.DictWriter(f, header_keys)
        dict_writer.writeheader()
        for dictlist in dictlistslist:
            dict_writer.writerows(dictlist)
    return None


def add_catches(stimlist,
                num_catches=10,
                shuffle_inlist=True):
    # TODO: docstring

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


def itis_shiftruncexpon(miniti=800.,
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


def add_jitter(stim_sequence,
               min_iti=.8,
               max_iti=1.5,
               av_iti=1.,
               jitter='shiftruncexpon'):
    """
    Add jittered inter trial intervals to a stimulus sequence.
    """
    if not jitter == 'shiftruncexpon':
        raise IOError('only the jitter type shifted truncated exponential is supported for now')
    itis = itis_shiftruncexpon(miniti=min_iti, maxiti=max_iti, aviti=av_iti, ntrials=len(stim_sequence))
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
        each list entry represents one stimulus gathered with get_stims_aloi_selection
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
        block_sequence = add_expinfo_stimsequence(block_sequence, experiment_info)
        block_sequence = add_empty_responses(block_sequence)
        block_sequence = add_catches(block_sequence)
        block_sequence = add_jitter(block_sequence, jitter='shiftruncexpon')
        for trial in block_sequence:
            trial['block'] = block
        run_sequences.append(block_sequence)

    return run_sequences


def present_run(run_sequence,
                output_csv,
                response_key='space',
                escape_key='escape',
                trigger_key='t',
                fullscreen=True,
                stimsize=(400, 400),
                fixdur=.500,
                stimdur=1.,
                skip_volumes=4):
    """
    # TODO: docstring
    # TODO: get monitor specifications from scanner and the viewing distance --> specify viewing angle!
    # TODO: use countdown timing (more precise)
    # TODO: transform presentation times into multiples of framerate, depends on monitor (but probably 60 Hz).
    """

    # # set up monitor
    # mon = monitors.Monitor('Iiyama', width=60.96, distance=60)
    # mon.setSizePix((1920, 1080))

    # Initiate  windows, stimuli, and alike
    window_ = visual.Window(color='black', fullscr=fullscreen, units='pix')  # monitor=mon
    event.Mouse(visible=False, win=window_)
    fixation = visual.ShapeStim(window_, size=20, lineWidth=5, closeShape=False, lineColor="white",
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

    # TODO: clarify how to deal with first few volumes. Discarded automatically? Or do I have to do so in my script?
    # what does this do with our stimulus onset timing?

    # do nothing during first few scans
    skipvol_instr = visual.TextStim(window_, text='dummy scans', color='white', height=20)
    skipvol_instr.draw()
    window_.flip()
    for i in range(skip_volumes):
        dummy_keys = event.waitKeys(keyList=[trigger_key], timeStamped=skipvol_time)

    # Wait for first scanner pulse
    firsttrig_instr = visual.TextStim(window_, text='waiting for first valid scanner pulse', color='white', height=20)
    firsttrig_instr.draw()
    window_.flip()
    firsttrig = event.waitKeys(keyList=[trigger_key], timeStamped=firsttrig_time)

    # block loop
    global_onset_time.reset()
    for stim_sequence in run_sequence:

        if escape_bool:
            print('escape bool was there')
            break

        # trial loop
        for trial in stim_sequence:

            if escape_bool:
                print('escape bool was there')
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
    # dictlist2csv(run_sequence, output_csv)

    # end presentation
    window_.close()
    core.quit()

    return None


def run_first_session(stimbasedir, outcsvdir, nruns=4, blocksprun=4, testing=False):
    # create output directory
    if not os.path.exists(outcsvdir):
        os.makedirs(outcsvdir)

    # get stim sequence
    perc_dir = pjoin(stimbasedir, 'percepts')
    prep_dir = pjoin(stimbasedir, 'preprocessed')
    percept_dicts, intact_dicts = get_stims_aloi_selection(percepts_dir=perc_dir, preprocessed_dir=prep_dir)

    # draw gui to get exp_info
    if testing:
        exp_info = OrderedDict({'Alter': ' 1', 'Geschlecht': 'weiblich', 'Rechtshaendig': True, 'Sitzung': '1',
                                'SubjectID': '1', 'date': u'2018_Nov_06_1408', 'exp_name': 'RI_RSA'})
    else:
        exp_info = show_gui(exp_name='RI_RSA')

    # TODO: instruction windows

    for run in range(1, nruns + 1):
        # make sequence for one run
        run_seq = make_run_seq(percept_dicts, exp_info, blocksperrun=blocksprun)
        # create csv file name (full path)
        csv_fname = pjoin(outcsvdir, 'sub%s_session%s_run%i.csv' % (exp_info['SubjectID'], exp_info['Sitzung'], run))
        # present one functional run
        present_run(run_seq, output_csv=csv_fname)

    return None


if __name__ == '__main__':
    stimdir = '/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/'
    outdir = os.path.dirname(os.path.realpath(__file__))

    run_first_session(stimbasedir=stimdir, outcsvdir=outdir, testing=True)

    # exp_info = OrderedDict({'Alter': ' 1', 'Geschlecht': 'maennlich', 'Rechtshaendig': True, 'Sitzung': 1,
    #                         'SubjectID': '1', 'date': u'2018_Nov_06_1408', 'exp_name': 'retina_rep'})
