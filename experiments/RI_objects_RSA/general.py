#!/usr/bin/python
# -*- coding: utf-8 -*-

import csv
import glob
import os
import random
import subprocess
from collections import OrderedDict

import numpy as np
from psychopy import gui, core, data, monitors, visual, event


def draw_gui(exp_name='RI_RSA',
             fields=(('SubjectID', ''), ('Gechlecht', ('maennlich', 'weiblich')),
                     ('Alter', ' '), ('Rechtshaendig', True), ('Sitzung', (1, 2)))):
    """
    Get session info from subject via a GUI.

    Parameters
    ----------
    exp_name : str
        Name of the experiment, will be stored in exp_info
    fields : tuple
        Questions presented in the gui. Tuple pairs correspond to key/value scheme of psychopy's gui dict.

    Returns
    -------
    exp_info : dict
        containing subject ID, gender, age, etc.
    """
    # initiate dict with information collected from GUI input
    exp_info = dict(fields)
    # draw gui
    dlg = gui.DlgFromDict(dictionary=exp_info, title=exp_name)
    # quit gui if user clicks 'cancel'
    if not dlg.OK:
        core.quit()
    # add additional info to exp_info which doesn't come from GUI input
    exp_info = OrderedDict(exp_info)
    exp_info['exp_name'] = exp_name
    exp_info['date'] = data.getDateStr()

    return exp_info


def id2name_dict():
    id2name = {
        '9': 'Schuh',
        '40': 'Gluehbirne',
        '89': 'Tube',
        '90': 'Ente',
        '125': 'Tasse',
        '161': 'Kanne',
        '263': 'Rahmen',
        '281': 'Knoblauch',
        '405': 'Locher',
        '408': 'Wuerfel',
        '461': 'Toilettenpapier',
        '466': 'Stift',
        '615': 'Dose',
        '642': 'Tacker',
        '910': 'Spruehflasche',
        '979': 'Hut'
    }
    return id2name


def getstims_aloiselection(percepts_dir='./Stimuli/percepts',
                           preprocessed_dir='./Stimuli/preprocessed',
                           id2namedict=id2name_dict()):
    """
    Create list of dicts containing information about all experimental stimuli, like their
    vision type ('ri_percept' vs. 'intact'), rotation, object_id and file_path.

    Parameters
    ----------
    percepts_dir : str
        Path to directory with RI percept images (should be .png).
    preprocessed_dir : str
        Path to directory with intact object images (which were also preprocessed in my case).
    id2namedict : dict
        for assigning object_names based on object_ids (because only object_ids are in the file names).

    Returns
    -------
    percept_dicts : list of dicts
        Each dict stands for one RI percept stimulus, containing key-value pairs for vision, rotation, object_id,
        object_name, and file path.
    intact_dicts : list of dicts
        Same as percept_dicts but for intact object stimuli.
    """
    #  check if input directory exists
    for directory in [percepts_dir, preprocessed_dir]:
        if not os.path.exists(directory):
            raise IOError('Could not find stimulus input directory : %s' % directory)

    # get files in directory
    percept_fpaths = glob.glob(percepts_dir + '/*.png')
    intact_fpaths = glob.glob(preprocessed_dir + '/*.png')

    # collect info from percept file names
    percept_dicts = []
    for percept_fpath in percept_fpaths:
        # vision1 and vision2 are not actually used for the dict
        object_id, rotation, vision1, vision2 = tuple(percept_fpath.split('/')[-1].split('.')[0].split('_'))
        percept_dict = OrderedDict({'file_path': percept_fpath,
                                    'object_id': object_id,
                                    'rotation': int(rotation.replace('r', '')),
                                    'vision': 'ri_percept'})
        percept_dicts.append(percept_dict)

    # collect info from intact (prepped) object file names
    intact_dicts = []
    for intact_fpath in intact_fpaths:
        object_id, rotation, vision = tuple(intact_fpath.split('/')[-1].split('.')[0].split('_'))
        intact_dict = OrderedDict({'file_path': intact_fpath,
                                   'object_id': object_id,
                                   'rotation': int(rotation.replace('r', '')),
                                   'vision': 'intact'})
        intact_dicts.append(intact_dict)

    # add object name
    for dictlist in [percept_dicts, intact_dicts]:
        for stimdict in dictlist:
            stimdict['object_name'] = id2namedict[stimdict['object_id']]

    return percept_dicts, intact_dicts


def add_trainingtest(percept_dicts,
                     intact_dicts):
    """
    Randomly choose half of the object stimuli and assign them to a 'training' or 'test' set.
    """

    objects = np.unique([stimdict['object_name'] for stimdict in percept_dicts])
    random.shuffle(objects)

    training_obs = objects[:len(objects) / 2]
    novel_obs = objects[len(objects) / 2:]

    for dictlist in [percept_dicts, intact_dicts]:
        for stimdict in dictlist:
            if stimdict['object_name'] in training_obs:
                stimdict['set'] = 'training'
            elif stimdict['object_name'] in novel_obs:
                stimdict['set'] = 'novel'
            else:
                raise KeyError('could not evaluate wether training or test object. stimulus is: %s'
                               % stimdict['file_path'])

    return percept_dicts, intact_dicts


def select_train(percept_dicts):
    selected = [pdict for pdict in percept_dicts if pdict['set'] == 'training']
    return selected


def mock_exp_info(which_session=2):
    """
    Create a dictionary containing dummy information for testing.
    """
    exp_info = OrderedDict({'Alter': ' 1', 'Geschlecht': 'weiblich', 'Rechtshaendig': True,
                            'Sitzung': str(which_session), 'SubjectID': '1', 'date': u'2018_Nov_06_1408',
                            'exp_name': 'RI_RSA'})
    return exp_info


def add_expinfo(stimsequence, exp_info):
    """
    Add key-value pairs in exp_info to list of stimdicts defined in stim_sequence so it will be
    captured in our logg files.
    """
    for stimdict in stimsequence:
        stimdict.update(exp_info)
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


def pick_monitor(mon_name='samsung_office'):
    """
    Create a psychopy monitor and window instance depending on where you want to display the experiment.
    """
    allowed = ['samsung_office', 'samsung_behavlab', 'soundproof_lab']
    if mon_name not in allowed:
        raise IOError('Could not find settings for mon : %s' % mon_name)
    mon, win = None, None
    if mon_name == 'samsung_office':
        res = (1920, 1080)
        mon = monitors.Monitor(mon_name, width=60., distance=60.)
        mon.setSizePix(res)
        win = visual.Window(monitor=mon, size=res, color='black', units='deg', screen=0, fullscr=True)
    elif mon_name == 'samsung_behavlab':
        res = (1920, 1080)
        mon = monitors.Monitor(mon_name, width=52.2, distance=60.)
        mon.setSizePix(res)
        win = visual.Window(monitor=mon, size=res, color='black', units='deg', screen=0, fullscr=True)
    elif mon_name == 'soundproof_lab':
        res = (1920, 1080)
        mon = monitors.Monitor(mon_name, width=53., distance=80.)  # cheat distance: 60, actual distance: 81.3
        mon.setSizePix(res)
        win = visual.Window(monitor=mon, size=res, color='black', units='deg', screen=0, fullscr=True)
    # mon.save()
    # TODO: 'skyra_projector'
    return mon, win


def movemouse_xdotool(psychopy_mon,
                      xoffset=0,
                      yoffset=230):
    """
    Execute shell command (xdotool) to reset mouse position when psychopy's pyglet module throws an error (as is
    the case in our soundproof_lab).

    Note that x and y coordinates start at zero in the upper left corner,
    so xoffset moves to the right, and yoffset moves down.
    """
    xres, yres = psychopy_mon.getSizePix()
    subprocess.Popen(["xdotool", "mousemove",
                      str((float(xres) / 2) + xoffset),
                      str((float(yres) / 2) + yoffset)])
    return None


def avoidcorner_xdotool(psychopy_mon,
                        xoffset=0,
                        yoffset=200,
                        quiesce=100):
    """
    Avoid annoying gnome feature (hot corners) that shows a workspace overview when the mouse hits the upper-left corner
    by simply re-positioning the mouse to a neutral position whenever this happens.
    """
    xres, yres = psychopy_mon.getSizePix()
    subprocess.Popen(['xdotool', 'behave_screen_edge', '--quiesce', str(quiesce), 'top-left', 'mousemove',
                      str((float(xres) / 2) + xoffset),
                      str((float(yres) / 2) + yoffset)])
    return None


def show_instr(window_instance,
               message="Lorem ipsum dolor sit amet.",
               textsize=.8,
               unit='deg',
               continue_key='space'):
    textstim = visual.TextStim(window_instance, height=textsize, units=unit, wrapWidth=40)
    textstim.setText(message)
    textstim.draw()
    window_instance.flip()
    event.waitKeys(keyList=[continue_key])
    return None
