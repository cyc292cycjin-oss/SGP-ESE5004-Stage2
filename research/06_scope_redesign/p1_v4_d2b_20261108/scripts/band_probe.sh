#!/bin/bash
# D2b section 3 probe: the D2a potential (t04) with the new source band rule (post_product) -> a temporary non-main table folder; compare the band shares
# with the committed D2a main folder out_ras (s30 shares). The temporary folder is moved out of the repository afterwards. No solver.
set -u
R=/home/jin/wt_v4_d2b; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; T=/home/jin/v4d2b
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
cd $R || exit 1
start=$(date +%s)
$PY scripts_project/v4_industry.py --work $T/work_probe --anchor-mode ras --set biomass_potential=v4_adjusted_t04 > $T/band_probe.log 2>&1; rc=$?
echo "EXIT:$rc seconds:$(( $(date +%s) - start ))" >> $T/band_probe.log
d=$(ls -d research_inputs/industry_v4/out_ras_* | while read x; do git ls-files --error-unmatch $x/V4_SWITCHES.json >/dev/null 2>&1 || echo $x; done | head -1)
echo "probe folder: $d" >> $T/band_probe.log
[ -n "$d" ] && { rm -rf $T/probe_out; mv $d $T/probe_out; }
$PY - >> $T/band_probe.log 2>&1 <<'P'
import json, pandas as pd
a = pd.read_csv("/home/jin/wt_v4_d2b/research_inputs/industry_v4/out_ras/INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
b = pd.read_csv("/home/jin/v4d2b/probe_out/INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
k = [f"biomass_source_band_{x}_share" for x in ("medium_a", "medium_b", "high")]
x = a[k].join(b[k], rsuffix="_new"); x["pe_bio"] = b.pe_biomass_mwh / 1e6; x["ov_ind"] = b.biomass_overflow_industry_mwh / 1e6; x["med_a_frac"] = b.medium_a_fraction
pd.set_option("display.width", 250); print(x.round(5).to_string())
other = [c for c in a.columns if c not in k]
d = [(c, cc) for c in other for cc in a.index if str(a.at[cc, c]) != str(b.at[cc, c])]
print("other differing cells:", d[:20], len(d))
j = json.load(open("/home/jin/v4d2b/probe_out/V4_SWITCHES.json")); print(j["switches"]); print(j["biomass_overflow_recomputed"]["VN"])
P
echo PROBE_DONE >> $T/band_probe.log
