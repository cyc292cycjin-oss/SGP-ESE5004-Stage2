#!/bin/bash
# run the read-only licence location check on the instance. Host and port from the calling command line environment only.
source /home/jin/s4n_ssh.sh
s4n_ssh bash -s < /home/jin/s4n_r_lic_check.sh
