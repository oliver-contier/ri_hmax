#!/usr/bin/python
# -*- coding: utf-8 -*-

import copy
import os
import random
from os.path import join as pjoin

import numpy as np
from psychopy import visual, event, core

from general import getstims_aloiselection, add_trainingtest, select_train, draw_gui, add_expinfo, \
    list_of_dictlists_2csv


def make_labelgrid_positions(downshift_all=.25,
                             downshift_upperrow=.1,
                             x_stretch=.1):
    lower_grid = [[-.5, 0], [0., 0.], [.5, 0], [-.5, -.5], [0, -.5], [.5, -.5]]
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


def add_distr_labels(stimdict_list, ndistractors=6, randorder=True):
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
               blocknumber):
    """
    Take our gathered subset of RI stimuli
    """
    behav_stims_copy = copy.deepcopy(behav_stims)
    random.shuffle(behav_stims_copy)
    behav_stims_copy = add_label_positions(behav_stims_copy)  # add target and distractor position
    behav_stims_copy = add_distr_labels(behav_stims_copy)  # add distractor labels
    behav_stims_copy = add_behav_responses(behav_stims_copy)
    for stimdict in behav_stims_copy:  # add block number
        stimdict['block'] = blocknumber
    return behav_stims_copy


def start_exp(nblocks=6,
              skipgui=False,
              showboxes=False,
              csv_outdir='./behav_data',
              img_size=(.5, .8),
              img_pos=(0, .5),
              escapekey='escape',
              maxtime=5,
              blanktime=.8,
              fixtime=.8,
              feedbacktime=2):
    # TODO: docstring
    # TODO: instruction windows at start and between blocks
    # TODO: get monitor specs from behav lab

    if not os.path.exists(csv_outdir):
        os.makedirs(csv_outdir)

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

    output_csv = pjoin(csv_outdir, 'sub%s_behav.csv' % exp_info_behav['SubjectID'])
    # get stimuli and generate list of block sequences
    stimuli = get_behav_stims(exp_info_behav)
    blocks = [make_block(stimuli, blocknum) for blocknum in range(1, nblocks + 1)]

    # monitor, window, mouse
    # mon = monitors.Monitor('Iiyama', width=60.96, distance=60)
    wind = visual.Window(color='black', fullscr=True)  # monitor=mon
    mouse = event.Mouse(win=wind)

    # initiate stimuli
    fix = visual.ShapeStim(wind, size=20, lineWidth=5, closeShape=False, lineColor="white", name='fixation',
                           units='pix', vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)))
    blank_ = visual.ShapeStim(wind, size=0, lineWidth=0, lineColor='black', name='blank')
    img_stim = visual.ImageStim(wind, size=img_size, pos=img_pos, name='image_stim')  # , units='pix')
    label_stim = visual.TextStim(wind, height=.1)  # alignVert='top',
    # create list of distractor boxes and one target box (boxes are invisible but clickable)
    box_kwargs = {'lineWidth': 3, 'width': .4, 'height': .3, 'opacity': 0, 'depth': -1.0, 'interpolate': True}
    targetbox = visual.Rect(win=wind, name='targetbox', lineColor='green', **box_kwargs)
    distboxes = [visual.Rect(win=wind, name='distbox_%i' % idx, lineColor='white', **box_kwargs)
                 for idx in range(1, 6)]

    # clocks
    timeout = core.Clock()
    blank_timer = core.Clock()
    fix_timer = core.Clock()
    feedback_timer = core.Clock()

    if showboxes:
        targetbox.setOpacity(1)
        for distbox in distboxes:
            distbox.setOpacity(1)

    # block loop
    escapebool = False
    for block in blocks:
        if escapebool:
            break

        # trial loop
        for trial in block:
            if escapebool:
                break

            # reset stuff
            keys = event.getKeys(keyList=[escapekey])
            mouse.setPos((0, 0))
            if not showboxes:
                targetbox.setOpacity(0)
                for distbox in distboxes:
                    distbox.setOpacity(0)

            # Show fixation
            fix_timer.reset()
            while fix_timer.getTime() < fixtime:
                fix.draw()
                wind.flip()

            # show display
            timeout.reset()
            while not trial['mouse_pressed'] and timeout.getTime() < maxtime:
                # draw image
                img_stim.setImage(trial['file_path'])
                img_stim.draw()
                # draw target label and box
                label_stim.setText(trial['object_name'])
                label_stim.setPos(trial['target_pos'])
                label_stim.draw()
                targetbox.setPos(trial['target_pos'])
                targetbox.draw()
                # draw distractor labels and boxes
                for distposition, distlabel, distbox in zip(trial['distr_pos'], trial['distractors'], distboxes):
                    label_stim.setPos(distposition)
                    label_stim.setText(distlabel)
                    label_stim.draw()
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
                targetbox.setOpacity(1)
                # draw image
                img_stim.setImage(trial['file_path'])
                img_stim.draw()
                # draw target label and box
                label_stim.setText(trial['object_name'])
                label_stim.setPos(trial['target_pos'])
                label_stim.draw()
                targetbox.setPos(trial['target_pos'])
                targetbox.draw()
                # draw distractor labels and boxes
                for distposition, distlabel, distbox in zip(trial['distr_pos'], trial['distractors'], distboxes):
                    label_stim.setPos(distposition)
                    label_stim.setText(distlabel)
                    label_stim.draw()
                    distbox.setPos(distposition)
                    distbox.draw()
                wind.flip()

            # show blank
            blank_timer.reset()
            while blank_timer.getTime() < blanktime:
                blank_.draw()
                wind.flip()

            # TODO: escape via escapekey
            if keys and escapekey in keys:
                escapebool = True

            trial['ran'] = True
            trial['keys'] = keys
            print(trial['accuracy'])
            print(trial['rt'])
            print(trial['clicked_distractor'])
            print(trial['keys'])

    # logg responses and trial info
    list_of_dictlists_2csv(blocks, output_csv)

    wind.close()
    core.quit()
    return None


if __name__ == '__main__':
    start_exp(skipgui=True, showboxes=False)
