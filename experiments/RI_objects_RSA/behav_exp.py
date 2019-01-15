#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Run the behavioral training part of the experiment by calling "start_exp()" at the end of this script.
Experiment parameters can be adjusted by choosing arguments for start_exp.
"""

import copy
import csv
import os
import random
# add different psychopy version to path
from os.path import join as pjoin

import numpy as np
from psychopy import visual, event, core

from misc import getstims_aloiselection, add_trainingtest, select_train, draw_gui, add_expinfo, \
    pick_monitor, show_instr, movemouse_xdotool, avoidcorner_xdotool


def make_labelgrid_positions(x_offset=12,
                             y_offset=8,
                             downshift_all=1,
                             downshift_upperrow=5,
                             x_stretch=-2.5):
    """
    Create grid coordinates to draw the labels on. Initial relative offsets can be set with x_offset and y_offset.
    The other parameters stretch and shift the resulting grid. All units in degree visual angle.
    """
    lower_grid = [[-x_offset, 0], [0., 0.], [x_offset, 0],  # upper row
                  [-x_offset, -y_offset], [0, -y_offset], [x_offset, -y_offset]]  # lower row
    # shift all labels down
    for labelpos in lower_grid:
        labelpos[1] -= downshift_all
    # shift only upper row down even further
    for labelpos in lower_grid[:len(lower_grid) / 2]:
        labelpos[1] -= downshift_upperrow
    # stretch along x axis
    lower_grid[0][0] -= x_stretch
    lower_grid[2][0] += x_stretch
    lower_grid[3][0] -= x_stretch
    lower_grid[5][0] += x_stretch
    return lower_grid


def add_label_positions(stim_sequence,
                        positions=make_labelgrid_positions()):
    """
    randomly assign (x,y) target coordinates to each stimulus under key word 'target_pos'
    and put the remaining possible coordinates into 'distr_pos'
    """
    for stimdict in stim_sequence:
        stimdict['target_pos'] = random.choice(positions)
        stimdict['distr_pos'] = [pos for pos in positions if not pos == stimdict['target_pos']]
    return stim_sequence


def add_distr_labels(stimdict_list,
                     ndistractors=6,
                     randorder=True):
    """
    Add distractor labels to stimulus dicts in a list.
    Each stimulus dict must already have an 'object_name' key.
    Distractors are chosen among all object names occuring in the list of stimuli.
    The number of distractors can be dialed down with ndistractors and their order can be randomized
    """
    # get names of all possible objects
    objects = np.unique([stimdict['object_name'] for stimdict in stimdict_list])
    # for each stimdict, remove target object and add subset of the remaining to the stim dicts 'distractors' key.
    for stimdict in stimdict_list:
        distractors = objects.tolist()
        distractors.remove(stimdict['object_name'])
        if randorder:
            random.shuffle(distractors)
        stimdict['distractors'] = distractors[:ndistractors]
    return stimdict_list


def get_behav_stims(experiment_info,
                    stimbasedir='./Stimuli'):
    """
    Create a stimulus sequence for the behavioral session. This stimulus sequence contains half of the RI percept
    stimuli.
    """
    # get (all) stimuli
    perceptsdir = pjoin(stimbasedir, 'percepts')
    preppeddir = pjoin(stimbasedir, 'preprocessed')
    percept_dicts, intact_dicts = getstims_aloiselection(preprocessed_dir=preppeddir, percepts_dir=perceptsdir)
    # select training stimuli
    percept_dicts, intact_dicts = add_trainingtest(percept_dicts, intact_dicts)
    behav_stimuli = select_train(percept_dicts)
    behav_stimuli = add_expinfo(behav_stimuli, experiment_info)  # add experiment info
    return behav_stimuli


def add_behav_responses(stim_sequence):
    """
    Add empty keys to each stimdict. The information will be filled in when each trial is run.
    """
    for stimdict in stim_sequence:
        stimdict['rt'] = None
        stimdict['accuracy'] = None
        stimdict['clicked_distractor'] = None
        stimdict['mouse_pressed'] = None
        stimdict['keys'] = None
        stimdict['ran'] = False
    return stim_sequence


def make_block(behav_stims,
               blocknumber,
               deepcopy=False,
               returnarray=True):
    """
    Take our gathered subset of RI stimuli and make it into a block sequence, by adding keys for labels and their
    positions, responses, and block number.

    Parameters
    ----------
    behav_stims : list
        list of behavioral stimuli, should be returned by get_behav_stims.
    blocknumber : int
        number of the current block. will be added as key to stimulus dicts.
    deepcopy : bool
        if true, creates a deepcopy of the original stimulus sequence. This way, you could be on the safe side that
        the original stims will not be messed up.
    returnarray : bool
        returns stimulus sequence as an array instead of a list.

    Returns
    -------
    behav_stims_copy : list
        list of stimulus dicts representing a block in the behavioral experiment.
    """
    if deepcopy:
        behav_stims_copy = copy.deepcopy(behav_stims)
    else:
        behav_stims_copy = behav_stims
    random.shuffle(behav_stims_copy)
    behav_stims_copy = add_label_positions(behav_stims_copy)  # add target and distractor position
    behav_stims_copy = add_distr_labels(behav_stims_copy)  # add distractor labels
    behav_stims_copy = add_behav_responses(behav_stims_copy)
    for stimdict in behav_stims_copy:  # add block number
        stimdict['block'] = blocknumber
    if returnarray:
        behav_stims_copy = np.array(behav_stims_copy)
    return behav_stims_copy


def start_exp(nblocks=6,
              skipgui=False,
              showtarget=False,
              csv_outdir='./behav_data',
              img_size=13,
              label_size=1.,
              img_pos=(0, 2.5),
              escapekey='q',
              maxtime=5.,
              blanktime=.8,
              fixtime=.8,
              feedbacktime=2,
              monitorname='samsung_office'):
    """
    Run the behavioral training part of the experiment.

    Parameters
    ----------
    nblocks : int
        number of blocks (each including one full repetition of stimulus set) the experiment should have.
    skipgui : bool
        if True, no gui will be presented and dummy subject + experiment info will be used instead.
        Only use this for testing purposes.
    showtarget : bool
        If True, always indicate the target with a green box. Only use for testing.
    csv_outdir : str
        Path to directory where output csv files are to be stored.
    img_size : int
        size of the RI percept image (in degree visual angle).
    label_size : int
        size of the text representing category labels (in degree visual angle).
    img_pos : tuple
        x/y coordinates of the image center (in degree visual angle)
    escapekey : str
        Key allowing user to escape the experiment. When experiment is escaped, a csv file will still be written!
    maxtime : float
        Maximum response time for the subject before next trial starts.
    blanktime : float
        duration of blank
    fixtime : float
        duration of fixation cross
    feedbacktime : float
        duration of feedback screen (i.e. green rectangle around correct category label)
    monitorname : str
        dummy name of used monitor (atm, only "samsung_office" and "samsung_behavlab" are allowed).

    Returns
    -------
    None
    """
    # Maximum Duration with timeout of 5s and 6 blocks ~ 42 min (including blanks and fix)
    # with 8 blocks, it would be maximum of 56 minutes

    # get experiment info (draw gui or dummy values for testing)
    if skipgui:
        exp_info_behav = {'SubjectID': 'test',
                          'Geschlecht': 'maennlich',
                          'Alter': '99',
                          'Rechtshaendig': True}
    else:
        guifields = {'SubjectID': '',
                     'Geschlecht': ('maennlich', 'weiblich'),
                     'Alter': '',
                     'Rechtshaendig': True}
        exp_info_behav = draw_gui(fields=guifields)

    if not os.path.exists(csv_outdir):
        os.makedirs(csv_outdir)
    output_csv = pjoin(csv_outdir, 'sub%s_behav.csv' % exp_info_behav['SubjectID'])

    # monitor, window, mouse
    if monitorname:
        mon, wind = pick_monitor(mon_name=monitorname)
    else:
        wind = visual.Window(color='black', colorSpace='rgb', units='deg', fullscr=True)
    mouse = event.Mouse(win=wind)

    # avoid ubuntu overview feature
    if monitorname == 'soundproof_lab':
        avoidcorner_xdotool(mon)

    # get stimuli and generate list of block sequences
    stimuli = get_behav_stims(exp_info_behav)

    # stimuli
    fix = visual.ShapeStim(wind, size=.8, lineWidth=3, closeShape=False, lineColor="white", name='fixation',
                           units="deg",
                           vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)))
    blank_ = visual.ShapeStim(wind, size=0, lineWidth=0, lineColor='black', name='blank')
    img_stim = visual.ImageStim(wind, size=img_size, pos=img_pos, name='image_stim', units='deg')
    distr_label = visual.TextStim(wind, height=label_size, units='deg', color='gray')
    target_label = visual.TextStim(wind, height=label_size, units='deg', color='gray')

    # list of distractor boxes and one target box (boxes are invisible but clickable)
    box_kwargs = {'lineWidth': 3, 'width': 8, 'height': label_size + .8,
                  'opacity': 1, 'depth': -1.0, 'interpolate': True, 'lineColor': 'gray'}
    distboxes = [visual.Rect(win=wind, name='distbox_%i' % idx, **box_kwargs) for idx in range(1, 6)]
    targetbox = visual.Rect(win=wind, name='targetbox', **box_kwargs)
    if showtarget:
        targetbox.setLineColor('green')

    # instruction text
    instr1 = """
    Vielen Dank, dass Sie an unserem Experiment teilnehmen.
    
    In dieser Studie moechten wir untersuchen, wie das menschliche Gehirn Objekte
    unter erschwerten Bedingungen erkennen kann.
    
    Dazu sehen Sie im Folgenden Bilder von alltaeglichen Objekten aus unterschiedlichen
    Blickwinkeln. Diese Bilder wurden so veraendert, dass sie dem Seheindruck eines
    Menschen mit Retinaimplantat moeglichst  genau entsprechen.
    
     Zu jedem Bild werden Ihnen ausserdem sechs moegliche Objektnamen angezeigt.
     Ihre Aufgabe besteht nun darin, mit der Maus auf den Namen des angezeigten
     Objekts zu klicken. Bitte versuchen Sie hierbei so schnell und korrekt wie moeglich
     zu antworten.
     
     <Weiter mit der Leertaste>
    """

    instr2 = """
    In jedem Durchgang haben Sie %s Sekunden Zeit, eine Antwort zu geben. Falls Sie in
    diesem Zeitfenster nicht reagieren, beginnt der naechste Durchgang.
    Ausserdem ehalten Sie nach jedem Durchgang Feedback ueber die korrekte Antwort.
    Dazu leuchtet die korrekte Antwortalternative gruen auf.
    
    Falls Sie noch Fragen haben, wenden Sie sich bitte jetzt an die Versuchsleitung
    
    <Weiter mit der Leertaste>
     """ % str(int(maxtime))

    # show welcoming instructions
    for instruction in [instr1, instr2]:
        show_instr(wind, message=instruction)

    # clocks
    timeout = core.Clock()
    blank_timer = core.Clock()
    fix_timer = core.Clock()
    feedback_timer = core.Clock()
    trialnum = 0

    # start csv writing
    dummyblock = make_block(stimuli, 99)
    header_keys = dummyblock[0].keys()
    dict_writer = csv.DictWriter(open(output_csv, 'wb'), header_keys)
    dict_writer.writeheader()

    # block loop
    escapebool = False
    for blocknum in range(1, nblocks + 1):

        # make block sequence
        block = make_block(stimuli, blocknum)

        if escapebool:
            break

        # show inter block instructions
        inter_block_message = "Als naechstes beginnt Block Nummer %i.\n\n" \
                              "Wenn Sie bereit sind, koennen Sie den naechsten Block selbststaendig starten.\n\n" \
                              "<Weiter mit der Leertaste> " % block[0]['block']
        show_instr(wind, message=inter_block_message)

        # trial loop
        for trial in block:
            trialnum += 1

            if escapebool:
                break

            # reset stuff
            keys = event.getKeys(keyList=[escapekey])
            target_label.setColor('gray')
            if not showtarget:
                targetbox.setLineColor('gray')
            if monitorname == 'soundproof_lab':
                movemouse_xdotool(mon)
            else:
                mouse.setPos((0, img_pos[1] - (img_size / 2) - 2))  # unit: degree vis angle

            # Show fixation
            fix_timer.reset()
            while fix_timer.getTime() < fixtime:
                fix.draw()
                wind.flip()

            # show display
            mouse.setVisible(1)
            timeout.reset()
            while not trial['mouse_pressed'] and timeout.getTime() < maxtime:
                # draw image
                img_stim.setImage(trial['file_path'])
                img_stim.draw()
                # draw target label and box
                target_label.setText(trial['object_name'])
                target_label.setPos(trial['target_pos'])
                target_label.draw()
                targetbox.setPos(trial['target_pos'])
                targetbox.draw()
                # draw distractor labels and boxes
                for distposition, distlabel, distbox in zip(trial['distr_pos'], trial['distractors'], distboxes):
                    distr_label.setPos(distposition)
                    distr_label.setText(distlabel)
                    distr_label.draw()
                    distbox.setPos(distposition)
                    distbox.draw()
                wind.flip()

                # response evaluation
                if mouse.isPressedIn(targetbox):
                    trial['mouse_pressed'] = True
                    trial['accuracy'] = 1
                    trial['rt'] = timeout.getTime()
                else:
                    trial['accuracy'] = 0
                    for distbox in distboxes:
                        if mouse.isPressedIn(distbox):
                            trial['mouse_pressed'] = True
                            trial['rt'] = timeout.getTime()
                            distidx = distboxes.index(distbox)
                            trial['clicked_distractor'] = trial['distractors'][distidx]

            # show feedback screen
            feedback_timer.reset()
            while feedback_timer.getTime() < feedbacktime:
                targetbox.setLineColor('green')
                # draw image
                img_stim.setImage(trial['file_path'])
                img_stim.draw()
                # draw target label and box
                target_label.setText(trial['object_name'])
                target_label.setPos(trial['target_pos'])
                target_label.setColor('green')
                target_label.draw()
                targetbox.setPos(trial['target_pos'])
                targetbox.draw()
                # draw distractor labels and boxes
                for distposition, distlabel, distbox in zip(trial['distr_pos'], trial['distractors'], distboxes):
                    distr_label.setPos(distposition)
                    distr_label.setText(distlabel)
                    distr_label.draw()
                    distbox.setPos(distposition)
                    distbox.draw()
                wind.flip()

            # show blank
            mouse.setVisible(0)
            blank_timer.reset()
            while blank_timer.getTime() < blanktime:
                blank_.draw()
                wind.flip()

            # escape via escapekey
            if keys and escapekey in keys:
                escapebool = True

            trial['ran'] = True
            trial['keys'] = keys
            print(trialnum)

            # write data of current trial
            dict_writer.writerow(trial)

    # # logg all data after loops have finished
    # nested_dictlist_2csv(blocks, output_csv)

    # final instruction screen
    show_instr(wind, "Vielen Dank! Das Experiment ist beendet.\n\n"
                     "Sie koennen sich jetzt an die Versuchsleitung wenden.")

    wind.close()
    core.quit()
    return None


if __name__ == '__main__':
    start_exp(monitorname='soundproof_lab')
