#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
hand-coded script for stimulus presentation in the scanner.
Include both first and second session and make adaptable by input GUI.
"""

import glob
import os
import random
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
        percept_dict = {'file_path': percept_fpath,
                        'object_ID': object_ID,
                        'rotation': int(rotation.replace('r', '')),
                        'vision': 'ri_percept'}
        percept_dicts.append(percept_dict)

    # collect info from intact (prepped) object file names
    intact_dicts = []
    for intact_fpath in intact_fpaths:
        object_ID, rotation, vision = tuple(intact_fpath.split('/')[-1].split('.')[0].split('_'))
        intact_dict = {'file_path': intact_fpaths,
                       'object_ID': object_ID,
                       'rotation': int(rotation.replace('r', '')),
                       'vision': 'intact'}
        intact_dicts.append(intact_dict)

    return percept_dicts, intact_dicts


def checkconsec(integerlist,
                assertlen=None):
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
                      exp_info,
                      response_key='space',
                      fullscreen=True,
                      windowsize=(1680, 1050),
                      stimsize=(400, 400),
                      fixdur=.500,
                      stimdur=1.,
                      blankdur=.500,
                      datapath='data'):
    """
    # TODO: docstring
    """

    """
    Initiate objects for window, fixation cross, stimulus, clocks, and trial handler.
    """

    # TODO: set window and stim size according to scanner hardware
    win = visual.Window(color='black', fullscr=fullscreen, units='pix')  # size=windowsize
    fixation = visual.ShapeStim(win, size=20,
                                vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)),
                                lineWidth=5,
                                closeShape=False,
                                lineColor="white")
    blank = visual.ShapeStim(win, size=0, lineWidth=0, lineColor='black')  # blank is empty shape stim
    stim = visual.ImageStim(win, size=stimsize)
    # contrast=1.0, opacity=1.0, depth=0

    trials = data.TrialHandler(stim_sequence, nReps=1, extraInfo=exp_info,
                               method='sequential', originPath=datapath)

    fix_rt = core.Clock()
    stim_rt = core.Clock()
    blank_rt = core.Clock()

    """
    loop through trials
    """
    for trial in trials:
        win.flip()
        print(trial)
        print(os.path.exists(trial['file_path']))

        # TODO: empty key press list at beginning of each trial
        # retrieve if this is a catch trial
        # TODO: don't create new variable to save computaitonal time
        if trial['trial_type'] == 'catch':
            catch = True
        elif trial['trial_type'] == 'normal':
            catch = False
        else:
            raise IOError('couldnt recognize trial_type : %s' % trial['trial_type'])

        # initiate responses
        acc = None
        rt = None
        escape_bool = False

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
            keys = event.waitKeys(maxWait=stimdur, keyList=[response_key, 'escape'],
                                  timeStamped=stim_rt.getTime())
            """
            Evaluate response
            """
            # exit if escape key was pressed
            if keys and 'escape' in keys[0]:
                print('USER ESCAPED')
                escape_bool = True
            # no response
            elif not keys:
                if not catch:
                    acc = 1
                if catch:
                    acc = 0
            # response given
            elif response_key in keys[0]:
                rt = stim_rt.getTime()
                if catch:
                    acc = 1
                if not catch:
                    acc = 0
            else:
                print('RESPONSE EVALUATION FAILED')
                escape_bool = True

            # add data to TrialHandler
            trials.addData('accuracy', acc)
            trials.addData('RT', rt)

        # TODO: show blank as jittered ITI
        blank_rt.reset()
        while blank_rt.getTime() < blankdur:
            blank.draw()
            win.flip()

        if escape_bool:
            break

    # end presentation
    # TODO: make output csv file name variable
    trials.saveAsWideText('testdata.csv', delim=',')
    win.close()

    return None


"""
dummy code for testing
"""
perc_dir = '/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/percepts'
prep_dir = '/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/preprocessed'

# exp_info, outfile = create_gui()
exp_info = {'Alter': ' 1', 'Gechlecht': 'maennlich', 'Rechtshaendig': True, 'Sitzung': 1, 'SubjectID': '1',
            'date': u'2018_Nov_06_1408', 'exp_name': 'retina_rep'}
percept_dicts, intact_dicts = get_stims_aloi_selection(percepts_dir=perc_dir, preprocessed_dir=prep_dir)
stim_seq = add_catches(percept_dicts)

win = visual.Window(color='black', fullscr=True, units='pix')  # size=windowsize
stim = visual.ImageStim(win)
stim.setImage('/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/test.png')
stim.draw()
win.flip()
core.wait(3)
win.close()

#loopthroughtrials(stim_seq, exp_info)


def runseq_deprecated(stimlist,
                      exp_info,
                      session,
                      datapath='data',
                      fixdur=1.,
                      stimdur=3.,
                      maskdur=1.,
                      fulls=True,
                      stimsize=(600, 400)):
    """
    Procedure of stimulus presentation. Initiates everything necessary and then loops through the trials.

    Parameters
    ----------
    stimlist : list of dicts
        Specifies stimulus sequence.
    exp_info : dict
        contains general info about the experiment, such as date, subject ID, etc.
    session : int
        First or second session.
    datapath : string
        relative path to data directory for output csv files.
    fixdur : float
        duration of fixation cross.
    stimdur : float
        duration of stimulus presentation.
    maskdur  float
        duration of mask image presented after stimulus.
    fulls : bool
        fullscreen mode?
    stimsize : tuple
        resolution of stimulus in pixels

    Returns
    -------
    None
    """

    """
    Initiate instances for window, fixation cross, and stimulus
    """

    win = visual.Window(size=(1680, 1050), color='black', fullscr=fulls, units='pix')
    fixation = visual.ShapeStim(win, size=20,
                                vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)),
                                lineWidth=5,
                                closeShape=False,
                                lineColor="white")
    stim = visual.ImageStim(win, size=stimsize)
    # list of random mask stimuli, generate beforehand for speed.
    maskstims = [create_maskstim(win, stimsize) for i in range(len(stimlist))]

    def _showtrial_deprecated(trial_instance, trialhandler, maskimg):
        """
        Sequence for one trial.
        """

        # retrieve if this is a catch trial
        catch = trial['catch']
        assert type(catch) == bool

        # initiate boolian to exit procedure with 'escape'
        escape_bool = False

        # initiate responses
        acc = None
        rt = None

        # show fixation
        fix_rt.reset()
        while fix_rt.getTime() < fixdur:
            fixation.draw()
            win.flip()

        # show stimulus
        stim.setImage(trial_instance['imagepath'])
        stim_rt.reset()
        while stim_rt.getTime() < stimdur:
            stim.draw()
            win.flip()
            keys = event.waitKeys(maxWait=stimdur, keyList=['space', 'escape'],
                                  timeStamped=stim_rt.getTime())
            """
            Evaluate response
            """
            # TODO: RT and accuracy is not written in csv file anymore .. fix that!
            # exit with escape key
            if keys and 'escape' in keys[0]:
                print('USER ESCAPED')
                escape_bool = True
            # no response
            elif not keys:
                if not catch:
                    acc = 1
                if catch:
                    acc = 0
            # response given
            elif keys:
                rt = stim_rt.getTime()
                if catch:
                    acc = 1
                if not catch:
                    acc = 0
            else:
                print('RESPONSE EVALUATION FAILED')
                escape_bool = True

            # add data to TrialHandler
            trialhandler.addData('accuracy', acc)
            trialhandler.addData('RT', rt)

        # show mask
        mask_rt.reset()
        while mask_rt.getTime() < maskdur:
            maskimg.draw()
            win.flip()

        return escape_bool

    """
    Loop through trials
    """

    # initiate timer for fixation cross and stimulus
    fix_rt = core.Clock()
    stim_rt = core.Clock()
    mask_rt = core.Clock()

    # initiate trial handler
    trials = data.TrialHandler(stimlist, nReps=1, extraInfo=exp_info,
                               method='sequential', originPath=datapath)

    # loop over trials
    for trial, mask in zip(trials, maskstims):
        # show trial
        escape_bool = _showtrial_deprecated(trial, trials, mask)
        # exit if escape was pressed
        if escape_bool:
            break

    # save csv
    csv_outfile = pjoin(datapath,
                        exp_info['SubjectID'] + '_' + exp_info['date'] + '_sitzung_' + str(session) + '.csv')
    print('saving output file')
    trials.saveAsWideText(csv_outfile, delim=',')

    # close window
    win.close()
