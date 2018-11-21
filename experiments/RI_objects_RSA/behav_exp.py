#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
from os.path import join as pjoin

import numpy as np
from psychopy import visual, event

from general import getstims_aloiselection, add_trainingtest, select_train, draw_gui, add_expinfo


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


def make_block(behav_stims,
               blocknumber):
    """
    Take our gathered subset of RI stimuli
    """
    random.shuffle(behav_stims)
    behav_stims = add_label_positions(behav_stims)  # add target and distractor position
    behav_stims = add_distr_labels(behav_stims)  # add distractor labels
    for stimdict in behav_stims:  # add block number
        stimdict['block'] = blocknumber
    return behav_stims


def start_exp(nblocks=6,
              test=False,
              img_size=(400, 400),
              img_pos=(0, 0.8),
              escapekey='escape'):
    # get experiment info (draw gui or dummy values for testing)
    if test:
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

    # get stimuli and generate list of block sequences
    stimuli = get_behav_stims(exp_info_behav)
    blocks = [make_block(stimuli, blocknum) for blocknum in range(1, nblocks + 1)]

    # TODO: define shape stimuli that sit behind every label position

    win = visual.Window(color='black', fullscr=True)  # , units='pix')  # monitor=mon
    mouse = event.Mouse(win=win)

    fix = visual.ShapeStim(win, size=20, lineWidth=5, closeShape=False, lineColor="white",
                           vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)))
    blank_ = visual.ShapeStim(win, size=0, lineWidth=0, lineColor='black')
    img_stim = visual.ImageStim(win, size=img_size, pos=img_pos, units='pix')
    label_stim = visual.TextStim(win, alignVert='top')

    catch_escape = event.getKeys(keyList=[escapekey])
    escapebool = False

    # block loop
    for block in blocks:

        if escapebool:
            break

        # trial loop
        for trial in block:

            if escapebool:
                break

            # draw image
            img_stim.setImage(trial['file_path'])
            img_stim.draw()

            # draw target label
            label_stim.setText(trial['object_name'])
            label_stim.setPos(trial['target_pos'])
            label_stim.draw()

            # draw distractor labels
            for position, label in zip(trial['distr_pos'], trial['distractors']):
                label_stim.setPos(position)
                label_stim.setText(label)
                label_stim.draw()

            win.flip()

            # TODO: response via mouse
            event.waitKeys(maxWait=10, keyList=list(['space']))

            if catch_escape and escapekey in catch_escape:
                escapebool = True

    return None


if __name__ == '__main__':
    # start_exp(test=True)

    # TODO: this test code works. Implement it in my trials.
    win = visual.Window(color='black', fullscr=True)  # , units='pix')  # monitor=mon

    mouse = event.Mouse(win=win)

    polygon = visual.Rect(
        win=win, name='polygon',
        width=(0.4, 0.4)[0], height=(0.4, 0.4)[1],
        ori=0, pos=(0, -.5),
        lineWidth=1, lineColor=[1, 1, 1], lineColorSpace='rgb',
        fillColor=[1, 1, 1], fillColorSpace='rgb',
        opacity=1, depth=-1.0, interpolate=True)

    pressed = False

    while not pressed:
        polygon.draw()
        win.flip()

        if mouse.isPressedIn(polygon):
            print('code arrived at ispressedin')
            pressed = True
        elif not mouse.isPressedIn(polygon):
            print('code arrived at notpressedin')
