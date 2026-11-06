cd /home/jin/wt_v4_fable || exit 1
echo "== RAS tol =="; grep -n "^RAS_TOL\|^RAS_MAX_ITER" scripts_project/m08b_demand.py
echo "== v3.1 heat-band summary VN: pe_biomass vs before overflow vs overflow =="
python3 - <<'PY'
import csv
for f in ["research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv", "research_inputs/industry_v4/out_ras/INDUSTRY_2050_SUMMARY_V4.csv"]:
    for r in csv.DictReader(open(f)):
        if r["country"] in ("VN",):
            print(f.split("/")[-1], r["country"], "pe_biomass", r["pe_biomass_mwh"], "before", r["pe_biomass_before_overflow_mwh"], "ov_ind", r["biomass_overflow_industry_mwh"], "ag50", r["agriculture_biomass_2050_mwh"], "pot", r["solid_biomass_potential_main_mwh"])
PY
echo "== v3.1 network VN overflow (package receipt) =="
python3 - <<'PY'
import json
r = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks/integrated_BUILD_RECEIPT.json"))
d = r.get("demand_s2", {})
ov = None
def find(o, depth=0):
    if isinstance(o, dict):
        if "overflow_industry_mwh" in o and "VN" in str(o)[:0]: pass
        for k, v in o.items():
            if k == "VN" and isinstance(v, dict) and "overflow_industry_mwh" in v:
                print("VN overflow ledger v3.1:", {kk: v[kk] for kk in ("industry_biomass_before_mwh", "agriculture_biomass_before_mwh", "cap_mwh", "overflow_industry_mwh")})
                return True
            if find(v, depth+1): return True
    return False
find(r)
PY
echo "== test files: any test for v4_tables refusal / process emissions table? =="; grep -ln "rerun v4_industry\|process_and_feedstock\|PROCESS_EMISSIONS" tests/research/test_v4_*.py; echo "(none above = gap)"
echo "== registry row v4_pks tier =="; grep "v4_pks_in_mill_share\|v4_national_balance" research_inputs/registry_v5/fragments/v4_w08.csv | cut -d, -f1,7,15
