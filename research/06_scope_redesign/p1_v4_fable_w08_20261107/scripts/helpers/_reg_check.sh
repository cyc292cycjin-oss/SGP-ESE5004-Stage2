set -u
T=/home/jin/v4fable; WT=/home/jin/wt_v4_fable; PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
export PYTHONHASHSEED=0
# research/ reference folders into the copy (tests need them)
mkdir -p $T/repo/research/06_scope_redesign
rsync -a $WT/research/06_scope_redesign/p1_v4_w07_20261106 $WT/research/06_scope_redesign/p1_v4_w08_20261106 $T/repo/research/06_scope_redesign/
echo "== registry: file rows sha check (own) =="
$PY - <<'PY'
import hashlib, pandas as pd
from pathlib import Path
R = Path("/home/jin/wt_v4_fable")
f = pd.read_csv(R/"research_inputs/registry_v5/fragments/v4_w08.csv", dtype=str, keep_default_na=False)
reg = pd.read_csv(R/"research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
bad = []; n = 0
for r in f.itertuples():
    if r.source_locator.startswith("file: "):
        p = R / r.source_locator[6:].split(" ")[0]; n += 1
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h != r.source_sha256: bad.append((r.param_id, str(p), h[:12], r.source_sha256[:12]))
        if r.unit == "bytes" and int(float(r.value)) != p.stat().st_size: bad.append((r.param_id, "bytes", r.value, p.stat().st_size))
print("file rows", n, "mismatches", bad)
# fragment rows == registry rows?
diff = []
for r in f.itertuples():
    if r.param_id not in reg.index: diff.append((r.param_id, "missing")); continue
    for c in f.columns:
        if c != "param_id" and str(reg.at[r.param_id, c]) != str(getattr(r, c)): diff.append((r.param_id, c))
print("fragment vs registry diffs", diff[:10], len(diff))
print("registry rows", len(reg), "fragment rows", len(f))
# status / tier summary
print(f.groupby(["tier","status"]).size())
PY
echo "== d1_registry reassembly in the copy =="
cd $T/repo && $PY scripts_project/d1_registry.py > $T/d1_registry.log 2>&1; echo "exit $?"; tail -2 $T/d1_registry.log | cut -c1-300
cmp $T/repo/research_inputs/registry_v5/DATA_REGISTRY.csv $WT/research_inputs/registry_v5/DATA_REGISTRY.csv && echo "DATA_REGISTRY.csv SAME as committed" || echo "DATA_REGISTRY.csv DIFFERS"
cmp $T/repo/research_inputs/registry_v5/D1_EVIDENCE.json $WT/research_inputs/registry_v5/D1_EVIDENCE.json && echo "D1_EVIDENCE.json SAME" || echo "D1_EVIDENCE.json DIFFERS"
echo "== registry diff aad8e476..7aa356e4 (removed/changed rows?) =="
cd $WT && git diff aad8e476 7aa356e4 --stat -- research_inputs/registry_v5/DATA_REGISTRY.csv research_inputs/registry_v5/D1_EVIDENCE.json
git diff aad8e476 7aa356e4 -- research_inputs/registry_v5/DATA_REGISTRY.csv | grep -c '^-[^-]' ; echo "(removed lines in DATA_REGISTRY.csv)"
git diff aad8e476 7aa356e4 -- research_inputs/registry_v5/D1_EVIDENCE.json | head -80
echo "== licence scan =="
grep -rniE "iea|world energy balance|calliope|\bWEB\b" research_inputs/industry_v4 research_inputs/biomass_v5/*V4* research_inputs/gas_v5/*V4* research_inputs/gas_v5/W12* research_inputs/demand_v5/NCV_EXCEPTIONS.csv research_inputs/demand_v5/DEMAND_ANCHOR_V3_* research_inputs/registry_v5/fragments/v4_w08.csv research_inputs/assembly_v1/sources/SDMX_* scripts_project/v4_*.py 2>/dev/null | grep -viE "ieaghg|hieа" | cut -c1-220 | head -20
echo "== network builds =="
ls -la /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds/*/*/ 2>/dev/null | head -40
cat /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds/BUILD_STATUS.txt 2>/dev/null | cut -c1-200
free -g | head -2
