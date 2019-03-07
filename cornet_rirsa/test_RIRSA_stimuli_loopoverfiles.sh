#! /usr/bin/bash

# declare array for layers
declare -a layers=("V1" "V2" "V4" "IT" "decoder")
# iterate over stimuli individually
for stim_dir in "./input_stimuli/RIRSA_stimuli/individual_stimuli"/*
do
  # create output directory
  out_dir="${stim_dir/input_stimuli/saved_features}"
  mkdir -pv $out_dir

  # iterate over layers
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
        --data_path $stim_dir \
        -o $out_dir

    # clean up temporary run script
    rm ./modified_run.py
  done


done
