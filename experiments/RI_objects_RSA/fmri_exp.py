#!/usr/bin/python

import os
from os.path import join as pjoin

from psychopy import event, visual, core

from fmri_sequences import make_rsa_run_sequence, load_glm_run
from misc import getstims_aloiselection, mock_exp_info, nested_dictlist_2csv, dictlist2csv
from psychopy_helper import pick_monitor, draw_gui
from instructions import next_block_instr, ending_instr, start_instr, part_two_instr


def present_run(run_sequence,
                output_csv,
                window_instance,
                runtype='ri_only',
                response_key='space',
                escape_key='escape',
                trigger_key='t',
                stimsize=13,  # 15,  # behav experiment uses 13 degree vis angle
                fixdur=.2,
                stimdur=1.1,
                skip_volumes=5,
                shift_responselog_back=1):
    """
    # TODO: docstring

    __run durations__

    # for stimdur=1.1, fixdur=.2, and average iti = 1.:
    - one all-stimuli run is about 10,4 minutes
    - one ri-only run is about 5,2 minutes
    """

    # Initiate  windows, stimuli, and alike
    event.Mouse(visible=False, win=window_instance)
    fixation = visual.ShapeStim(window_instance, size=1, lineWidth=5, closeShape=False, lineColor="white", units='deg',
                                vertices=((0, -0.5), (0, 0.5), (0, 0), (-0.5, 0), (0.5, 0)))
    blank = visual.ShapeStim(window_instance, size=0, lineWidth=0, lineColor='black')
    stim = visual.ImageStim(window_instance, size=stimsize, units='deg')
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
    firsttrig_instr = visual.TextStim(window_instance, text='waiting for first scanner pulse',
                                      color='white', height=1, units='deg')
    firsttrig_instr.draw()
    window_instance.flip()
    firsttrig = event.waitKeys(keyList=[trigger_key], timeStamped=firsttrig_time)  # firsttrig looks like [['t', 1.43]]
    global_onset_time.reset()

    # do nothing during first few scans.
    skipvol_instr = visual.TextStim(window_instance, text='dummy scans',
                                    color='white', height=1, units='deg')
    skipvol_instr.draw()
    window_instance.flip()
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
                window_instance.flip()

            # show stimulus
            stim.setImage(trial_seq[idx]['file_path'])
            trial_seq[idx]['global_onset_time'] = global_onset_time.getTime()
            stim_rt.reset()
            while stim_rt.getTime() < stimdur:
                stim.draw()
                window_instance.flip()

            # show jittered blank
            blank_rt.reset()
            while blank_rt.getTime() < trial_seq[idx]['iti']:
                blank.draw()
                window_instance.flip()

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
        nested_dictlist_2csv(run_sequence, csv_fname=output_csv)
    # no nested loop necessary for runs wich present both stim types
    if runtype == 'ri_and_intact':
        # present trials
        escape_bool = _present_trials(run_sequence)
        # add additional global info to trial dicts
        for trial_ in run_sequence:
            trial_['first_trigger'] = firsttrig[0][1]
            trial_['last_dummy_trigger'] = dummy_keys[0][1]
        # write output csv
        dictlist2csv(run_sequence, output_csv)

    return escape_bool


def start_fmri_experiment(stimbasedir='./Stimuli',
                          outcsvdir='./fmri_logs',
                          n_rsa_runs=4,
                          reps_per_rsa_run=1,
                          rsa_iti_min=.8,
                          rsa_iti_max=1.5,
                          rsa_iti_av=1.,
                          n_glm_runs=3,
                          stim_dur=1.1,
                          fix_dur=.2,
                          test=False,
                          responsekey='1',
                          triggerkey='t',
                          startkey='space',
                          textsize=1.,
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

    mon, win = pick_monitor(mon_name)

    # draw gui to get exp_info
    if test:
        exp_info = mock_exp_info(which_session=2)
    else:
        exp_info = draw_gui(exp_name='RI_RSA')

    # get session number from gui input
    session_int = int(exp_info['Sitzung'])
    assert session_int in [1, 2]

    # present very first instruction window
    start_instr(window_instance=win, text_size=textsize)

    # present runs which only contain ri percepts (used in both sessions)
    for run in range(1, n_rsa_runs + 1):
        # make a sequence for this subject
        run_seq = make_rsa_run_sequence(percept_dicts, exp_info, reps_per_run=reps_per_rsa_run,
                                        miniti=rsa_iti_min, maxiti=rsa_iti_max, aviti=rsa_iti_av)
        # create csv file name
        csv_fname = pjoin(outcsvdir, 'sub%s_session%s_rionly_run%i_fmri.csv'
                          % (exp_info['SubjectID'], exp_info['Sitzung'], run))
        # show inter-block instructions. Press 'space' before starting the scanner sequence.
        next_block_instr(run_nr=run, window_instance=win, continuekey=startkey, text_size=textsize)
        # present one functional run
        escape_bool = present_run(run_seq, output_csv=csv_fname, window_instance=win,
                                  runtype='ri_only', response_key=responsekey, trigger_key=triggerkey,
                                  stimdur=stim_dur, fixdur=fix_dur)

        # quit experiment if escape key was pressed
        if escape_bool:
            print('experiment quit via escape key.')
            ending_instr(window_instance=win, text_size=textsize)
            win.close()
            core.quit()

    # if this is session 2, present the runs with all stimuli (intact and ri percept)
    # which are loaded from efficiency optimization results.
    if session_int == 2:
        # load the sequence for this subject
        glm_runs = load_glm_run(sub_id=exp_info['SubjectID'], nruns=n_glm_runs)
        # show short instruction about the second part of the fmri experiment (i.e. intact and ri stimuli)
        part_two_instr(win, text_size=textsize)
        # iterate through runs
        for run in glm_runs:
            # make output csv file name
            csv_fname = pjoin(outcsvdir, 'sub%s_session%s_allstim_run%i_fmri.csv'
                              % (exp_info['SubjectID'], exp_info['Sitzung'], glm_runs.index(run) + 1))
            # show inter-run instructions
            next_block_instr(run_nr=glm_runs.index(run) + 1, window_instance=win,
                             continuekey=startkey, text_size=textsize)
            # present this run
            escape_bool = present_run(run, output_csv=csv_fname, window_instance=win,
                                      runtype='ri_and_intact', response_key=responsekey, trigger_key=triggerkey,
                                      stimdur=stim_dur, fixdur=fix_dur)
            # break glm-run loop if escape key was pressed
            if escape_bool:
                break

    # end of experiment
    ending_instr(window_instance=win, text_size=textsize)
    win.close()
    core.quit()

    return None


if __name__ == '__main__':
    start_fmri_experiment(reps_per_rsa_run=1, n_rsa_runs=4, n_glm_runs=3, stim_dur=1.1, mon_name='samsung_office',
                          test=True)  # TODO: remove test=True when actually running