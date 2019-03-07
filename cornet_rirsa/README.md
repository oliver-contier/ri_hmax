# Using the CORnet to extract image features

These scripts utilize the CORnet model by Kubilius et al. (2018) to extract image features from the stimuli presented in our fMRI study. Based on these image features, visual model dissimilarity matrices will be constructed and used in the representational similarity analysis.

## References

Kubilius, J., Schrimpf, M., Nayebi, A., Bear, D., Yamins, D. L., & DiCarlo, J. J. (2018). CORnet: Modeling the Neural Mechanisms of Core Object Recognition. BioRxiv, 408385. https://doi.org/10.1101/408385


## Installation and requirements

for convenience, create a new anaconda environment from the requirements.txt.

```
conda env create -n cornet_env python=3.7 --file requirements.txt
conda activate cornet_env
```

Alternatively, you may install requirements and the cornet package manually (see https://github.com/dicarlolab/CORnet).

```
conda create -n cornet_env python=3.7
conda activate cornet_env
pip install git+https://github.com/dicarlolab/CORnet
conda install PyTorch numpy pandas tqm
conda install fire -c conda-forge
```


## Usage

There are two possibilities to run feature extraction on the stimuli. 1) The CORnet run script can be called on all stimuli at once. 2) The CORnet run script can be called on each individual input image, producing one .npy output file per image and layer.

Option 1) is more efficient and more consistent with the design of CORnet. Option 2) however makes absolutely sure which output corresponds to which stimulus. Hence, for the purpose of this study, we chose to work with the output of option 2).

### Option 1)

```
bash test_rirsa_stimulu_allatonce.sh
```

### Option 2)
```
bash test_rirsa_stimulu_loopoverfiles.sh
```
