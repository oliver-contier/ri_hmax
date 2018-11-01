# RI_HMAX

This repository contains scripts for analyzing simulated retinal implant percepts to quantify how much information is preserved when a natural image is transformed by a retinal implant. 

This idea originated from a data reanalysis of an already existing experiment within the lab for experimental psychology at Otto-von-Guericke University Magdeburg (Germany). The stimuli and data of the original experiment are not uploaded to github for reasons of data protection.

Apart from the exploratory scripts and notebooks found here, I will try to assemble a more modular codebase for future use.

Some of the methods here rely heavily on the implementation of the HMAX model which was developed by Thomas Miconi and retrieved from <a href="https://scholar.harvard.edu/tmiconi/pages/code">here</a> in July 2018. Explicit permission to use these scripts is still pending, though the scripts were freely available from the mentioned website. Until we get explicit permission, I will keep this repository private.

## Reanalysis of Lihui's study

To compute different types of typicality from Lihui's study and predict behavioral outcomes with them, run the following in order:
- runallhmax_serial.py
- neural_typicality.ipynb
- data_exploration.ipynb
- lme4_modelfit.R
- lme4_analysis.ipynb

## ALOI stimuli

I also wrote some scripts to explore viewpoint typicality of over 200 selected objects from the ALOI data base. This endeavor is not finished yet, but you can already use condor to create RI percepts of loads of stimuli at once (using Johannes' supersim) and obtain respective HMAX outputs. Just use aloi_submitall.py with argument 'supersim' or 'hmax' for that.

### TODO: Calculate typicalities of ALOI selection.    