#!/usr/bin/python

import os
from os.path import join as pjoin

from psychopy import event, visual, core

from fmri_exp_functions import make_rsa_run_sequence
from general import pick_monitor, list_of_dictlists_2csv, getstims_aloiselection, mock_exp_info, draw_gui


def present_run_by_iti(run_sequence,
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
    # TODO: docstring

    # TODO: IMPORTANT My presentation function can only present trials using their ITIs. Make it also work for my GLM runs, which have pre-determined onsets!

    # TODO: get monitor specifications from scanner (resolution, width, viewing distance, etc.)
    """

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
    for i in range(skip_volumes - 1):
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
        exp_info = mock_exp_info()
    else:
        exp_info = draw_gui(exp_name='RI_RSA')

    # TODO: instruction windows

    for run in range(1, nruns + 1):
        # make sequence for one run
        run_seq = make_rsa_run_sequence(percept_dicts, exp_info, blocksperrun=blocksprun)
        # create csv file name (full path)
        csv_fname = pjoin(outcsvdir,
                          'sub%s_session%s_run%i_fmri.csv' % (exp_info['SubjectID'], exp_info['Sitzung'], run))
        # present one functional run
        present_run_by_iti(run_seq, output_csv=csv_fname, monitorname=mon_name)

    return None


if __name__ == '__main__':
    stimdir = '/Users/Oliver/ri_hmax/experiments/RI_objects_RSA/Stimuli/'
    outdir = os.path.dirname(os.path.realpath(__file__))
    run_first_session(stimbasedir=stimdir, outcsvdir=outdir, mon_name='samsung_office', testing=True)
