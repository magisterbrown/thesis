#!/bin/bash
# Sort + spreading CPU time (thread-seconds) for default, full selection and S_max-only selection,
# with the per-thread bin-sort and spreader timers. 3D S_max-only picks equal the full selection's, so are not rerun.
# usage: imc_sw.sh <threads> <uni|exp> <full picks> <S_max-only picks> <out file>
cd ~/finufft-timers
thr=$1; dist=$2; full=$3; spo=$4; out=$5; touch $out
export PERFTEST_ALLOW_EPS=1 PERFTEST_SPREADONLY=1 FINUFFT_PHASE_TIMERS=1
if [ $dist = exp ]; then export PERFTEST_DIST=exp; else unset PERFTEST_DIST; fi
paste -d' ' $full $spo | while read d p de n bx by bz sp _ _ _ _ _ _ _ _ sx sy sz ssp _ _ _ _; do
  F1=$((2*n)); F2=1; F3=1; [ $d -ge 2 ] && F2=$((2*n)); [ $d -eq 3 ] && F3=$((2*n))
  M=$(python3 -c "print(int($de*$n**$d))")
  cfgs="dflt:0:0:0:0 best:$bx:$by:$bz:$sp"
  [ $d -lt 3 ] && cfgs="$cfgs sponly:$sx:$sy:$sz:$ssp"
  for r in 1 2; do for cfg in $cfgs; do
    IFS=: read tg x y z s <<< "$cfg"
    grep -q "^d$d prec$p dens$de r$r $tg " $out && continue
    ./build/perftest/perftest --prec=$p --N1=$F1 --N2=$F2 --N3=$F3 --M=$M --tol=1e-7 --threads=$thr --upsampfact=2 \
      --type=1 --n_runs=2 --max_sp_size $s --binsize_x $x --binsize_y $y --binsize_z $z 2>&1 |
      grep -E "^\[(phase|busy|sort_phase|sort_busy)\]" |
      sed "s/^/d$d prec$p dens$de r$r $tg bins$x,$y,$z sp$s M$M /" >> $out
  done; done
done
echo DONE >> $out
