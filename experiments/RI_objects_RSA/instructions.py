#!/usr/bin/python
"""
Convenience functions for presenting the instructions during the fMRI experiment.
"""

from psychopy import visual, event


def show_instr(window_instance,
               message="Lorem ipsum dolor sit amet.",
               textsize=.8,
               textpos=(0., 0.),
               unit='deg',
               continue_key='space'):
    """
    Generic function to show instructions until continue_key is pressed.
    """
    textstim = visual.TextStim(window_instance, height=textsize, units=unit, wrapWidth=40, pos=textpos)
    textstim.setText(message)
    textstim.draw()
    window_instance.flip()
    event.waitKeys(keyList=[continue_key])
    return None


def start_instr(window_instance, continuekey='space', text_size=1.):
    """
    The very first instructions to be shown in the fmri experiment.
    """
    show_instr(window_instance=window_instance, textsize=text_size, unit='deg', continue_key=continuekey,
               message="Bitte warten Sie, das Experiment beginnt in Kuerze")
    return None


def next_block_instr(run_nr, window_instance, continuekey='space', text_size=1.):
    """
    Helper function to present instruction between functional runs.
    Continuekey must be pressed before the scanner sequence is started!
    """
    show_instr(window_instance=window_instance, textsize=text_size, continue_key=continuekey,
               message="Als naechstes beginnt Block % i. Bitte warten Sie einen Moment." % run_nr)
    return None


def part_two_instr(window_instance, continuekey='space', text_size=1.):
    """
    Instruction before commencing to the second part of the experiment, where both ri and intact stimuli are shown.
    This only occurs in session 2.
    """
    show_instr(window_instance=window_instance, textsize=text_size, unit='deg', continue_key=continuekey,
               message="Als naechstes beginnt der zweite Teil unseres Experiments.\n"
                       "Sie sehen nun sowohl simulierte Retinaimplantat-Bilder, als auch \n"
                       "gewoehnliche, unveraenderte Objekte. Ihre Aufgabe bleibt dabei dieselbe.")
    return None


def ending_instr(window_instance, continuekey='space', text_size=1.):
    """
    present instruction that the experiment has ended.
    """
    show_instr(window_instance=window_instance, textsize=text_size, continue_key=continuekey,
               message="Vielen Dank, das Experiment ist nun vorbei. \n"
                       "Bitte warten Sie auf die Versuchsleitung.")
    return None
