#!/usr/bin/env bash

echo "sourcing env"
source /home/contier/ri_hmax_env/bin/activate
echo "which python : "
which python

echo "input file : "
echo $1
echo "output file : "
echo $2

echo "executing supersim_handler.py"
python supersim_handler.py $1 $2