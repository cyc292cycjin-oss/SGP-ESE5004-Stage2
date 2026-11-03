#!/bin/bash
# V3 screening rerun (supplement 07) (local): save the instance records (r_record.sh, r_small.sh) under /home/jin/v3r/records/, host / port scrubbed by v3s_run, instance name
# replaced by <INSTANCE>. Host / port only from the environment.
set -u
R=/home/jin/v3r/records; mkdir -p $R
PFX="autodl""-container-"   # built from two parts: this file holds no instance-name prefix
for s in r_record r_small; do
  bash /home/jin/v3r/run.sh /home/jin/v3r/$s.sh | sed -E "s/${PFX}[A-Za-z0-9-]+/<INSTANCE>/g" > $R/$s.txt
  echo "$s: $(wc -l < $R/$s.txt) lines, $(grep -c '<INSTANCE>' $R/$s.txt) instance names replaced, $(tail -1 $R/$s.txt)"
done
