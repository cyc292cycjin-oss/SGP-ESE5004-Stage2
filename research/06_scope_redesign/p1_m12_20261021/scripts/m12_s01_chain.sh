#!/bin/bash
# M12 supplement 01 evidence chain (sequential: one LP build at a time; nothing is solved)
L=/home/jin/m12_local/s01_chain.log
echo "START $(date -Is)" > $L
for s in m08b_variants:"TH LA BN ID KH MM MY PH SG TL" smoke s4n365 s4o365 benefit m08b_int m08b_dis m08b_loo365:"VN TH LA" m08b_loo24:"BN ID KH MM MY PH SG TL"; do
  st=${s%%:*}; cs=""; [ "$st" != "$s" ] && cs=${s#*:}
  if [ -n "$cs" ]; then STEP=$st COUNTRIES="$cs" bash /home/jin/m12_s01.sh >> $L 2>&1; else STEP=$st bash /home/jin/m12_s01.sh >> $L 2>&1; fi
  echo "== $st done $(date -Is)" >> $L
done
echo "END $(date -Is)" >> $L
echo DONE >> $L
