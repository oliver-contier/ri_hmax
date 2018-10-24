#!/usr/bin/env bash

echo "sourcing env"
source /home/contier/ri_hmax_env/bin/activate

echo "executing supersim_handler.py"
python supersim_handler.py $1 $2