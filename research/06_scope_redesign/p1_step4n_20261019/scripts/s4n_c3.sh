#!/bin/bash
# S4N-2 environment (CLOUD_DEPLOY_STEPS section 3 points 2-3): apt tmux / GNU time / util-linux; conda env pypsa-earth from the package yml, in the
# background on the instance (nohup; log /root/autodl-tmp/s4n_conda.log). No solve. Skipped when the env already exists with the right versions.
# Host and port from the calling command line environment only.
set -u
source /home/jin/s4n_ssh.sh
s4n_ssh 'export DEBIAN_FRONTEND=noninteractive; [ -f /etc/network_turbo ] && source /etc/network_turbo >/dev/null 2>&1; (apt-get update -qq >/tmp/s4n_apt_update.log 2>&1 || echo APT_UPDATE_FAILED); apt-get install -y -qq tmux time util-linux >/tmp/s4n_apt_install.log 2>&1; echo "APT_EXIT=$?"; tail -2 /tmp/s4n_apt_install.log; ls -l /usr/bin/time; tmux -V; command -v setsid'
s4n_ssh 'cat > /root/autodl-tmp/s4n_conda.sh <<"R"
#!/bin/bash
# S4N: conda environment from the S4M package (no solve)
cd /root/autodl-tmp/s4m_cloud
[ -f /etc/network_turbo ] && source /etc/network_turbo
echo "CONDA_START:$(date "+%F %T")"
if [ -x /root/miniconda3/envs/pypsa-earth/bin/python ]; then echo "ENV_EXISTS (not recreated)"; echo "CONDA_EXIT:0"; else /root/miniconda3/bin/conda env create -n pypsa-earth -f environment_pypsa-earth.yml; echo "CONDA_EXIT:$?"; fi
echo "CONDA_END:$(date "+%F %T")"
R
chmod +x /root/autodl-tmp/s4n_conda.sh; nohup bash /root/autodl-tmp/s4n_conda.sh > /root/autodl-tmp/s4n_conda.log 2>&1 &
sleep 5; head -5 /root/autodl-tmp/s4n_conda.log'
