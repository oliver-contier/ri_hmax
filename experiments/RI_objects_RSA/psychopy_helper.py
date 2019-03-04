#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Contains miscellaneous helper functions that use psychopy.
"""

import subprocess
from collections import OrderedDict

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
    exp_info['date'] = data.getDateStr().encode('utf-8')

    return exp_info


def pick_monitor(mon_name='samsung_office',
                 bgcolor='black',
                 screen_index=0,
                 fullscreen=True):
    """
    Create a psychopy monitor and window instance depending on where you want to display the experiment.
    """
    allowed = ('samsung_office', 'samsung_behavlab', 'soundproof_lab', 'skyra_projector')
    if mon_name not in allowed:
        raise IOError('Could not find settings for mon : %s' % mon_name)
    if mon_name == 'samsung_office':
        res = (1920, 1080)
        wid = 60.
        dist = 60.
    elif mon_name == 'samsung_behavlab':
        res = (1920, 1080)
        wid = 52.2
        dist = 60.
    elif mon_name == 'soundproof_lab':
        res = (1920, 1080)
        wid = 53.
        dist = 80.
    elif mon_name == 'skyra_projector':
        # experimenter machine monitor has 24", so width 53 cm and same resolution
        res = (1920, 1080)
        wid = 37
        dist = 36.5
    else:
        raise IOError('could not find monitor with name %s' % mon_name)
    mon = monitors.Monitor(mon_name, width=wid, distance=dist)
    mon.setSizePix(res)
    # mon.save()
    win = visual.Window(monitor=mon, size=res, color=bgcolor, units='deg', screen=screen_index, fullscr=fullscreen)

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
