#!/bin/bash
cd /home/jin/wt_v3_hpc
sha256sum research_inputs/registry_v5/DATA_REGISTRY.csv research_inputs/registry_v5/fragments/v3.csv
git log --oneline -1 -- research_inputs/registry_v5/DATA_REGISTRY.csv
/home/jin/miniforge3/envs/pypsa-earth/bin/python - <<'P'
import json, netCDF4
ds = netCDF4.Dataset("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_op/integrated/integrated_2920_3h_unsolved.nc"); meta = json.loads(ds.getncattr("meta")); ds.close()
def walk(d, p=()):
    if isinstance(d, dict):
        for k, v in d.items():
            if "registry" in str(k).lower(): print(".".join(p + (str(k),)), str(v)[:120])
            walk(v, p + (str(k),))
walk(meta)
P
