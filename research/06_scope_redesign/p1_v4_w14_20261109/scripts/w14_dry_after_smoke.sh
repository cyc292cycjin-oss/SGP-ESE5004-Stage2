#!/bin/bash
# W14 section 3.2 ("0 NOTE"): the guide's step D1 check in the smoke-drill copy AFTER the smoke passed - hpc/hpr_submit.sh --dry-run with an authorisation file and
# a placeholder licence path (mode 600; existence / mode only). This machine has no qsub; hpr_submit.sh only tests `command -v qsub` in a dry run and never calls it,
# so a STUB named qsub is put first on PATH that refuses to run (prints STUB_QSUB_CALLED and exits 99) - any call would show. Expected: 3 qsub lines, 0 DRY-RUN NOTE,
# "0 check(s) above would refuse a real submission". Run once with bash and once with bash 4.2. No solver, nothing submitted.
# usage: w14_dry_after_smoke.sh <smoke drill folder /home/jin/v4w14/smoke_<stamp>>
set -u
S=${1:?smoke drill folder}; P=$S/pkg; [ -f "$P/runs/smoke56_v4/SMOKE_STATUS.txt" ] || { echo "no smoke status in $P"; exit 2; }
T=$S/after_dry; mkdir -p $T/stub; printf '%s\n' '#!/bin/bash' 'echo STUB_QSUB_CALLED; exit 99' > $T/stub/qsub; chmod 755 $T/stub/qsub
printf '%s\n' "local drill authorisation placeholder for the dry-run check" > $T/auth.txt; echo placeholder > $T/fake_lic; chmod 600 $T/fake_lic
cd $P || exit 2
for BB in bash /home/jin/v3h/bash42/src/bash; do
  PATH=$T/stub:$PATH GRB_LICENSE_FILE=$T/fake_lic $BB hpc/hpr_submit.sh --auth-file $T/auth.txt --motd-checked --dry-run > $T/out_$(basename $BB).txt 2>&1; rc=$?
  echo "AFTER_SMOKE_DRY_RUN:shell=$($BB --version | head -1 | cut -c1-40):exit=$rc:qsub_lines=$(grep -c '^DRY-RUN: qsub' $T/out_$(basename $BB).txt):notes=$(grep -c '^DRY-RUN NOTE' $T/out_$(basename $BB).txt):stub_called=$(grep -c STUB_QSUB_CALLED $T/out_$(basename $BB).txt):runs_batch6=$( [ -e runs/batch6 ] && echo yes || echo no)"
  cat $T/out_$(basename $BB).txt
done
