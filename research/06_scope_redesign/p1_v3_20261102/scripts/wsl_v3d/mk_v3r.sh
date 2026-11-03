#!/bin/bash
# V3 supplement 07 section 2.2: the session folder of the cloud rerun, /home/jin/v3r, copied from the first screening (/home/jin/v3s) with the rerun paths:
# package screen_package_v3_dmax (commit fbdf2c2e), instance folder /root/autodl-tmp/v3_screen_dmax (the first batch folder untouched), watchdog folder
# /root/autodl-tmp/v3_watchdog_dmax, run list V1 V2 V3. No auth text, no records and no analysis outputs are copied. No host / port anywhere.
set -e
S=/home/jin/v3s; R=/home/jin/v3r
[ ! -e $R ] || { echo "REFUSED: $R exists"; exit 2; }
mkdir -p $R/records
cp $S/*.sh $S/*.py $R/
cd $R
sed -i -e 's#/home/jin/v3s/#/home/jin/v3r/#g' -e 's#/root/autodl-tmp/v3_screen_auth\.txt#/root/autodl-tmp/v3_screen_dmax_auth.txt#g' \
       -e 's#/root/autodl-tmp/v3_screen_guard_names\.txt#/root/autodl-tmp/v3_screen_dmax_guard_names.txt#g' -e 's#/root/autodl-tmp/v3_screen\b#/root/autodl-tmp/v3_screen_dmax#g' \
       -e 's#/root/autodl-tmp/v3_watchdog\b#/root/autodl-tmp/v3_watchdog_dmax#g' -e 's#screen_package_v3_op#screen_package_v3_dmax#g' -e 's#55253dd7#fbdf2c2e#g' \
       -e 's#for r in V1 V2 V4 V5 V3#for r in V1 V2 V3#g' -e 's#V3 screening#V3 screening rerun (supplement 07)#' *.sh *.py
echo "files: $(ls | wc -l)"
echo "== remaining references to the first batch (must be none outside comments of the analysis scripts):"
grep -nE "/root/autodl-tmp/v3_screen([^_]|$)|/home/jin/v3s|55253dd7|screen_package_v3_op|v3_watchdog([^_]|$)" *.sh *.py | cut -c1-160 || echo "none"
echo "== key lines"
grep -hE "^SRC=|^P=|^RUN=|^O=|DST=|v3_screen_dmax_auth" upload.sh r_verify.sh r_status.sh v3s_watchdog.sh lic.sh | cut -c1-200
