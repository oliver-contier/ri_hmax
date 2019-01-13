#!/usr/bin/python

import os
from os.path import join as pjoin

from psychopy import event, visual, core

from fmri_exp_functions import make_rsa_run_sequence, load_glm_run
from general import pick_monitor, getstims_aloiselection, mock_exp_info, draw_gui, list_of_dictlists_2csv, dictlist2csv


def present_run(run_sequence,
                output_csv,
                runtype='ri_only',
                response_key='space',
                escape_key='escape',
                trigger_key='t',
                stimsize=13,  # 15,  # behav experiment uses 13 degree vis angle
                fixdur=.2,  # .500,
                stimdur=.8,  # 1.,
                skip_volumes=5,
                monitorname='skyra_projector',
                shift_responselog_back=1):
    """
    # TODO: docstring
    # TODO: get monitor specifications from scanner (resolution, width, viewing distance, etc.)
    """

    # Initiate  windows, stimuli, and alike
    mon, window_ = pick_monitor(monitorname)
    event.Mouse(visible=False, win=window_)
    fixation = visual.ShapeStim(window_, size=1, lineWidth=5, closeShape=False, lineColor="white", units='deg',
                                vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)))
    blank = visual.ShapeStim(window_, size=0, lineWidth=0, lineColor='black')
    stim = visual.ImageStim(window_, size=stimsize, units='deg')
    escape_bool = False
    dummy_keys = None

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

    # Wait for first scanner pulse.
    firsttrig_instr = visual.TextStim(window_, text='waiting for first scanner pulse',
                                      color='white', height=1, units='deg')
    firsttrig_instr.draw()
    window_.flip()
    firsttrig = event.waitKeys(keyList=[trigger_key], timeStamped=firsttrig_time)  # firsttrig looks like [['t', 1.43]]
    global_onset_time.reset()

    # do nothing during first few scans.
    skipvol_instr = visual.TextStim(window_, text='dummy scans',
                                    color='white', height=1, units='deg')
    skipvol_instr.draw()
    window_.flip()
    for i in range(skip_volumes - 1):
        dummy_keys = event.waitKeys(keyList=[trigger_key], timeStamped=skipvol_time)

    """
    Start task
    """

    def _present_trials(trial_seq, escapebool=escape_bool, shift_response_log_back=shift_responselog_back,
                        responsekey=response_key, escapekey=escape_key):
        """
        Helper function to present a series of trials. This can be used flexibly to handle nested or simple lists
        of trials. In this experiment, this reflects in the two different run types (idx: multiple blocks of the
        ri percept stimuli, or ii: one block of all stimuli).
        """

        # trial loop
        for idx in range(len(trial_seq)):

            if escapebool:
                break

            # somehow, I have a bug where each response is attributed to the next trial instaed of the current one.
            # this indexing workaround fixes that.
            idx_before = idx - shift_response_log_back

            # capture keyboard input, time stamp with clock stim_rt
            responses = event.getKeys(keyList=[responsekey, escapekey], timeStamped=stim_rt)

            # show fixation
            fix_rt.reset()
            while fix_rt.getTime() < fixdur:
                fixation.draw()
                window_.flip()

            # show stimulus
            stim.setImage(trial_seq[idx]['file_path'])
            trial_seq[idx]['global_onset_time'] = global_onset_time.getTime()
            stim_rt.reset()
            while stim_rt.getTime() < stimdur:
                stim.draw()
                window_.flip()

            # show jittered blank
            blank_rt.reset()
            while blank_rt.getTime() < trial_seq[idx]['iti']:
                blank.draw()
                window_.flip()

            # response evaluation
            if idx_before >= 0:
                trial_seq[idx_before]['responses'] = responses
                if responses:
                    trial_seq[idx_before]['RT'] = responses[0][1]
                    if trial_seq[idx_before]['trial_type'] == 'normal':
                        trial_seq[idx_before]['accuracy'] = 0
                    elif trial_seq[idx_before]['trial_type'] == 'catch':
                        trial_seq[idx_before]['accuracy'] = 1
                else:
                    if trial_seq[idx_before]['trial_type'] == 'normal':
                        trial_seq[idx_before]['accuracy'] = 1
                    elif trial_seq[idx_before]['trial_type'] == 'catch':
                        trial_seq[idx_before]['accuracy'] = 0
            # exit loop if escape key was pressed
            if responses:
                for response in responses:
                    if escapekey in response:
                        escapebool = True

            # mark this trial as ran
            trial_seq[idx]['ran'] = True

        # propagate escapebool so we can break out of nested loop
        return escapebool

    # decide what type of run this is
    assert runtype in ['ri_only', 'ri_and_intact']
    if runtype == 'ri_only':
        # loop through blocks within this run
        for trial_sequence in run_sequence:
            if escape_bool:
                break
            # present runs
            escape_bool = _present_trials(trial_sequence)
            # add additional info to the results
            for trial_ in trial_sequence:
                trial_['first_trigger'] = firsttrig[0][1]
                trial_['last_dummy_trigger'] = dummy_keys[0][1]
        # write csv file
        list_of_dictlists_2csv(run_sequence, csv_fname=output_csv)
    # no nested loop necessary for runs wich present both stim types
    if runtype == 'ri_and_intact':
        # present trials
        escape_bool = _present_trials(run_sequence)
        # write output csv
        dictlist2csv(run_sequence, output_csv)
        # add additional global info to trial dicts
        for trial_ in run_sequence:
            trial_['first_trigger'] = firsttrig[0][1]
            trial_['last_dummy_trigger'] = dummy_keys[0][1]

    # end presentation
    window_.close()
    core.quit()

    return None


def start_fmri_experiment(stimbasedir,
                          outcsvdir,
                          n_rsa_runs=4,
                          reps_per_rsa_run=2,
                          test=False,
                          mon_name='skyra_projector'):
    """
    """
    # TODO: docstring
    # create output csv directory
    if not os.path.exists(outcsvdir):
        os.makedirs(outcsvdir)

    # get stimulus dicts
    perc_dir = pjoin(stimbasedir, 'percepts')
    prep_dir = pjoin(stimbasedir, 'preprocessed')
    percept_dicts, intact_dicts = getstims_aloiselection(percepts_dir=perc_dir, preprocessed_dir=prep_dir)

    # draw gui to get exp_info
    if test:
        exp_info = mock_exp_info(which_session=2)
    else:
        exp_info = draw_gui(exp_name='RI_RSA')

    # TODO: present instruction windows

    # get session number from gui input
    session_int = int(exp_info['Sitzung'])
    assert session_int in [1, 2]

    # present runs which only contain ri percepts (used in both sessions)
    for run in range(1, n_rsa_runs + 1):
        run_seq = make_rsa_run_sequence(percept_dicts, exp_info, reps_per_run=reps_per_rsa_run)
        run_seq = run_seq
        csv_fname = pjoin(outcsvdir, 'sub%s_session%s_rionly_run%i_fmri.csv'
                          % (exp_info['SubjectID'], exp_info['Sitzung'], run))
        # present one functional run
        present_run(run_seq, output_csv=csv_fname, monitorname=mon_name, runtype='ri_only')

    # if this is session 2, present the runs with all stimuli (intact and ri percept)
    # which are loaded from efficiency optimization results.
    if session_int == 2:
        # load the sequence for this subject
        glm_runs = load_glm_run(sub_id=exp_info['SubjectID'])
        for run in glm_runs:
            csv_fname = pjoin(outcsvdir, 'sub%s_session%s_allstim_run%i_fmri.csv'
                              % (exp_info['SubjectID'], exp_info['Sitzung'], glm_runs.index(run) + 1))
            present_run(run, output_csv=csv_fname, monitorname=mon_name, runtype='ri_and_intact')

    return None


if __name__ == '__main__':
    outdir = os.path.dirname(os.path.realpath(__file__))
    start_fmri_experiment(stimbasedir='./Stimuli', outcsvdir='./fmri_logs', mon_name='samsung_office', test=True)
