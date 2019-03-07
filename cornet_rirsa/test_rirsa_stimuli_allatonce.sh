#!/usr/bin/env bash

# conda activate cornet_env

# declare array to iterate through layers (note: there is no V3 in CORnet)
declare -a layers=("V1" "V2" "V4" "IT" "decoder")

# iterate through layers
for layer in "${layers[@]}"
do

  # create new temporary run script
  cp ./CORnet/run.py ./modified_run.py
  # search and replace desired layer
  sed -i -e "s/layer='V1'/layer='$layer'/g" \
    ./modified_run.py

  # run it to extract features
  echo $layer
    python ./modified_run.py test \
      --restore_path cornet_s_epoch43.pth.tar - --model S \
      --data_path input_stimuli/RIRSA_stimuli/all/ \
      -o saved_features

  # clean up temporary run script
  rm ./modified_run.py
done
