#!/bin/bash
# X20 ①7：（1）改后的 d1_biomass.py / v4_biomass_potential.py 不带开关运行 = 复现（重写已跟踪的输出，git 须无差异）；（2）--v5-residue-fix 写 V5FIX 表；（3）逐国对照。
set -u
R=/home/jin/wt_v5_x20; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111; LOG=$D/logs/52_biomass_v5fix.log
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
cd $R/scripts_project || exit 1
{
echo "== (1) reproduction (v4 mode)"
$PY d1_biomass.py > $D/cache/d1_biomass_v4.log 2>&1; echo "d1_biomass exit $?"
$PY v4_biomass_potential.py > $D/cache/v4_biomass_potential_v4.log 2>&1; echo "v4_biomass_potential exit $?"
cd $R; echo "git status after the v4-mode reruns (must be empty):"; git status --short research_inputs | grep -v "^??" ; echo "(end)"
cd $R/scripts_project
echo "== (2) --v5-residue-fix"
$PY d1_biomass.py --v5-residue-fix; echo "exit $?"
$PY v4_biomass_potential.py --v5-residue-fix | tail -3; echo "exit $?"
$PY - <<'P'
import pandas as pd
B = "/home/jin/wt_v5_x20/research_inputs/biomass_v5/"
a = pd.read_csv(B + "BIOMASS_POTENTIAL_2050.csv"); b = pd.read_csv(B + "BIOMASS_POTENTIAL_2050_V5FIX.csv")
a6 = pd.read_csv(B + "BIOMASS_POTENTIAL_2050_V4_T06.csv"); b6 = pd.read_csv(B + "BIOMASS_POTENTIAL_2050_V4_T06_V5FIX.csv")
f = lambda d: d[d.feedstock_group != "biogas"].groupby("country").potential_main_mwh.sum() / 1e6
t = pd.DataFrame(dict(v3_base_TWh=f(a), v5fix_base_TWh=f(b), t06_TWh=f(a6), t06_v5fix_TWh=f(b6)))
t["d_t06_TWh"] = t.t06_v5fix_TWh - t.t06_TWh
print(t.round(4).to_string()); print("ASEAN d_t06 TWh", round(float(t.d_t06_TWh.sum()), 4))
c = a[(a.country == "MM")].set_index("category").potential_main_mwh.sub(b[(b.country == "MM")].set_index("category").potential_main_mwh, fill_value=0) / 1e6
print("MM base change by category (TWh, v4 - v5fix):"); print(c[c.abs() > 1e-9].round(4).to_string())
print(pd.read_csv(B + "BIOMASS_CROSSCHECK_IRENA_V5.csv").round(3).to_string(index=False))
P
cd $R; git status --short research_inputs/biomass_v5
} > $LOG 2>&1
cat $LOG
