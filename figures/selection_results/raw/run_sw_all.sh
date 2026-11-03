#!/bin/bash
cd ~/finufft-timers
for s in "20 uni uni20" "10 uni uni10" "1 uni uni1" "20 exp exp20"; do
  set -- $s
  ./imc_sw.sh $1 $2 sw/picks_full_$3.txt sw/picks_sp_$3.txt sw/sw_$3.txt
done
echo ALLDONE > sw/all_done.txt
