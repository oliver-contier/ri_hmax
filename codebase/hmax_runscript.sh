#!/usr/bin/env bash
echo "sourcing env"
source /home/contier/hmax_p27_env/bin/activate
echo "which python : "
which python

echo "input file file : "
echo $1
echo "output file : "
echo $2

echo "executing hmax_handler.py"
python hmax_handler.py $1 $2