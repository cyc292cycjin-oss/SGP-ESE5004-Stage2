set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; S=/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107; WT=/home/jin/wt_v4_fable; T=/home/jin/v4fable
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds
cd $WT || exit 1
echo "################ S7 COMPARE"; $PY $S/scripts/s7_compare.py $T/cp_ras/step_S7.json $T/cp_iid/step_S7.json $WT/research/06_scope_redesign/p1_v4_w08_20261106 $S/evidence/S7_COMPARE.json 2>&1 | tail -32
echo "################ ANCHOR / PROFILES"; $PY $S/scripts/anchor_profile_check.py $WT $S/evidence/ANCHOR_PROFILE_CHECK.json 2>&1 | tail -95
echo "################ NET iid"; $PY $S/scripts/net_check.py $B/iid/integrated/integrated_2920_3h_unsolved.nc $WT out_iid $S/evidence/NET_CHECK_iid.json 2>&1 | grep -v "^INFO" | grep -E "max\|diff\||overflow|gas caps|meta sha|rail" 
echo "################ 365x24h vs 2920x3h industry load, TH bagasse SDMX"; $PY - <<PY
import warnings; warnings.filterwarnings("ignore")
import pypsa, numpy as np, xml.etree.ElementTree as ET
n3 = pypsa.Network("$B/main/integrated/integrated_2920_3h_unsolved.nc"); n24 = pypsa.Network("$B/main/integrated/integrated_365_24h_unsolved.nc")
print("365 snapshots", len(n24.snapshots), "weights", n24.snapshot_weightings.generators.iloc[0])
for l in ["ID_Java-Bali1 0 industry electricity demand", "VN2 0 industry heat high demand"]:
    if l in n3.loads_t.p_set.columns and l in n24.loads_t.p_set.columns:
        a = n3.loads_t.p_set[l].to_numpy().reshape(365, 8).mean(1); b = n24.loads_t.p_set[l].to_numpy()
        print(l, "daily mean of 3h == 24h series:", float(np.abs(a - b).max()), "energy 3h", float((n3.loads_t.p_set[l] * 3).sum()), "24h", float((n24.loads_t.p_set[l] * 24).sum()))
    else:
        print(l, "in 3h:", l in n3.loads_t.p_set.columns, "in 24h:", l in n24.loads_t.p_set.columns, "static p_set 24h", float(n24.loads.p_set.get(l, float("nan"))))
NS={"g":"http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}
root=ET.parse("$WT/research_inputs/assembly_v1/sources/unsd_sdmx_2019/TH_2019_all.xml").getroot()
for s in root.iter("{%s}Series" % NS["g"]):
    key={v.get("id"):v.get("value") for v in s.find("g:SeriesKey",NS)}
    if key.get("COMMODITY")=="5120":
        for o in s.findall("g:Obs",NS):
            print("TH bagasse", key["TRANSACTION"], o.find("g:ObsValue",NS).get("value"))
PY
