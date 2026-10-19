#!/bin/bash
# copy the post-processing tools (no host / port / licence in them) to /root/autodl-tmp/s4n_tools on the instance; syntax-check them there.
set -u
source /home/jin/s4n_ssh.sh
s4n_ssh 'mkdir -p /root/autodl-tmp/s4n_tools' || exit 1
s4n_scp -q /home/jin/s4n_r_post.sh /home/jin/s4n_pilot_check.py /home/jin/s4n_c1_precision.py "root@$S4N_HOST:/root/autodl-tmp/s4n_tools/" || { echo "SCP FAILED"; exit 1; }
s4n_ssh 'cd /root/autodl-tmp/s4n_tools && bash -n s4n_r_post.sh && echo SH_SYNTAX_OK; /root/miniconda3/envs/pypsa-earth/bin/python -m py_compile s4n_pilot_check.py s4n_c1_precision.py && echo PY_SYNTAX_OK; ls -la | grep -v total'
