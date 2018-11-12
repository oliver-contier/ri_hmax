#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
hand-coded script for stimulus presentation in the scanner.
Include both first and second session and make adaptable by input GUI.
"""

import csv
import glob
import os
import random
from collections import OrderedDict
from os.path import join as pjoin

from psychopy import gui, core, data, visual, event


def create_gui(out_dir='./data',
               exp_name='retina_rep'):
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

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

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

    # output file path
    outfile = pjoin(out_dir, exp_info['SubjectID'] + '_' + exp_info['date'] + '_sitzung_' + str(exp_info['Sitzung']))

    return exp_info, outfile


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


def add_catches(stimlist,
                num_catches=10,
                shuffle_inlist=True):
    # TODO: docstring

    # assert that we didn't specify too many catch trials given our constraints
    assertplus2(stimlist, range(num_catches))
    # make copy of original list
    stimlist_copy = list(stimlist)
    # shuffle if desired
    if shuffle_inlist:
        random.shuffle(stimlist_copy)
    # add key-value indicating if this is a catch or normal trial
    for stim in stimlist_copy:
        stim['trial_type'] = 'normal'

    # make list of random, non-consecutive positions for catch trials
    # with constraint that first and last trials mustn't be catch trials
    consec_bool, firstlast_bool = True, True
    while consec_bool or firstlast_bool:
        catchpositions = random.sample(range(len(stimlist_copy)), num_catches)
        consec_bool, firstlast_bool = checkconsec(catchpositions), checkfirstlast(catchpositions, stimlist_copy)

    # choose items in new_stimlist (i.e. percept_dict) that should be followed by catch trials
    catchstims = [stimlist_copy[pos] for pos in catchpositions]

    # add trial_type information to catch stimuli
    for catchstim in catchstims:
        catchstim['trial_type'] = 'catch'

    # insert catchstims into list at appropriate index
    for catchstim in catchstims:
        stimlist_copy.insert(stimlist_copy.index(catchstim) + 1, catchstim)

    return stimlist_copy


def loopthroughtrials(stim_sequence,
                      output_csv='testdata.csv',
                      response_key='space',
                      escape_key='escape',
                      fullscreen=True,
                      windowsize=(1680, 1050),
                      stimsize=(400, 400),
                      fixdur=.500,
                      stimdur=1.,
                      blankdur=.500):
    """
    # TODO: docstring
    """

    # Initiate  window, fixation cross, stimulus, clocks, and trial handler.
    win = visual.Window(color='black', fullscr=fullscreen, units='pix')  # size=windowsize
    fixation = visual.ShapeStim(win, size=20,
                                vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)),
                                lineWidth=5,
                                closeShape=False,
                                lineColor="white")
    blank = visual.ShapeStim(win, size=0, lineWidth=0, lineColor='black')  # blank is empty shape stim
    stim = visual.ImageStim(win, size=stimsize)
    # trials = data.TrialHandler(stim_sequence, nReps=1, extraInfo=exp_info, method='sequential', originPath=datapath)

    # clocks
    # TODO: logg time passed overall
    fix_rt = core.Clock()
    stim_rt = core.Clock()
    blank_rt = core.Clock()

    # trial loop
    for trial in stim_sequence:

        # wait for keyboard input
        keys = event.getKeys(keyList=[response_key, escape_key], timeStamped=stim_rt.getTime())

        # show fixation
        fix_rt.reset()
        while fix_rt.getTime() < fixdur:
            fixation.draw()
            win.flip()

        # show stimulus
        stim.setImage(trial['file_path'])
        stim_rt.reset()
        while stim_rt.getTime() < stimdur:
            stim.draw()
            win.flip()

        # response evaluation
        trial['keys'] = keys
        if keys:
            if escape_key in keys[0]:
                break
            trial['RT'] = keys[0][1]
            if trial['trial_type'] == 'normal':
                trial['accuracy'] = 0
            elif trial['trial_type'] == 'catch':
                trial['accuracy'] = 1
        else:
            if trial['trial_type'] == 'normal':
                trial['accuracy'] = 1
            elif trial['trial_type'] == 'catch':
                trial['accuracy'] = 0

        # TODO: show blank as jittered ITI
        blank_rt.reset()
        while blank_rt.getTime() < blankdur:
            blank.draw()
            win.flip()
        # tag this trial as presented
        trial['ran'] = True

    # write output csv
    header_keys = stim_sequence[0].keys()
    with open(output_csv, 'wb') as f:
        dict_writer = csv.DictWriter(f, header_keys)
        dict_writer.writeheader()
        dict_writer.writerows(stim_sequence)

    # end presentation
    win.close()
    core.quit()

    return None


if __name__ == '__main__':
    """
    dummy code for testing
    """
    perc_dir = '/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/percepts'
    prep_dir = '/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/preprocessed'

    # exp_info, outfile = create_gui()
    exp_info = OrderedDict({'Alter': ' 1', 'Geschlecht': 'maennlich', 'Rechtshaendig': True, 'Sitzung': 1, 'SubjectID': '1',
                'date': u'2018_Nov_06_1408', 'exp_name': 'retina_rep'})

    percept_dicts, intact_dicts = get_stims_aloi_selection(percepts_dir=perc_dir, preprocessed_dir=prep_dir)

    # TODO: function to add exp_info and response vars o stimulus dicts. Maybe include in add_catches.
    for stimdicts in [percept_dicts, intact_dicts]:
        for stimdict in stimdicts:
            stimdict.update(exp_info)

    # initiate empty responses in each stimulus dict
    for trial_num, stimdict in enumerate(percept_dicts):
        stimdict['RT'] = None
        stimdict['accuracy'] = None
        stimdict['keys'] = None
        stimdict['trial_num'] = trial_num
        stimdict['ran'] = False

    # add catches to sequence
    stim_seq = add_catches(percept_dicts)

    # start stimulus presentation loop
    loopthroughtrials(stim_seq, exp_info)
