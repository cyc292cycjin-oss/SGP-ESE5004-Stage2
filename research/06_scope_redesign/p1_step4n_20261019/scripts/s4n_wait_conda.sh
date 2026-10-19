#!/bin/bash
# poll the instance until the conda env creation ends (CONDA_EXIT in the log), then print the package versions; max 75 min per call
source /home/jin/s4n_ssh.sh
for i in $(seq 1 150); do
  out=$(s4n_ssh 'tail -c 600 /root/autodl-tmp/s4n_conda.log 2>/dev/null' 2>&1)
  if echo "$out" | grep -q "CONDA_EXIT:"; then
    echo "$out" | tr '\r' '\n' | tail -8
    s4n_ssh '/root/miniconda3/envs/pypsa-earth/bin/python - <<"P" 2>&1 | grep -v PROJ
import sys, importlib
print("python", sys.version.split()[0])
for m in ("pypsa", "linopy", "gurobipy", "numpy", "pandas", "xarray", "scipy", "netCDF4"):
    mod = importlib.import_module(m); print(m, getattr(mod, "__version__", None) or ".".join(map(str, mod.gurobi.version())))
P
du -sh /root/miniconda3/envs/pypsa-earth | cut -f1'
    exit 0
  fi
  sleep 30
done
echo "STILL_RUNNING after 75 min"; echo "$out" | tr '\r' '\n' | tail -5
