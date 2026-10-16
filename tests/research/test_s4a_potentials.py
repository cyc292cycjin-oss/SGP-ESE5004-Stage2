"""S4A-3 (L16): candidate potential audit - sources registered, nothing applied to the network, candidate costs consistent."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PV = ROOT / "research_inputs/potentials_v5"
FRAG = ROOT / "research_inputs/registry_v5/fragments/potentials_s4a.csv"


def test_fragment_rows_and_status():
    f = pd.read_csv(FRAG, keep_default_na=False)
    assert f.param_id.is_unique and (f.source_sha256 != "").all()
    assert set(f.status) <= {"REFERENCE_ONLY", "CANDIDATE_ONLY", "DATA_PENDING", "SOURCE_ZERO"}   # nothing REGISTERED: potentials are not applied
    pend = f[f.status == "DATA_PENDING"]
    assert (pend.value == "DATA_PENDING").all() and pend.description.str.contains("Impact").all()
    for pid in ["potential_geothermal_ID_resource_potential", "potential_hydro_VN_pdp8_total_potential", "potential_hydro_PH_doe_resource_assessments", "potential_hydro_MM_adb_identified_projects"]:
        assert pid in set(f.param_id)


def test_site_candidates_still_zero_and_nuclear_unbounded():
    import yaml
    cfg = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())["research"]
    for k in ["geothermal", "ror_new", "hydro_new", "PHS_new"]:
        assert cfg["site_candidates"][k]["p_nom_max"] == 0.0 and cfg["site_candidates"][k]["status"] == "DATA_PENDING"
    assert cfg["nuclear"]["smr"]["p_nom_max"] == float("inf")


def test_cost_consistency_and_evidence():
    c = pd.read_csv(PV / "CANDIDATE_COST_CONSISTENCY.csv")
    assert c.consistent.all() and set(c.technology) >= {"nuclear", "nuclear SMR", "geothermal", "hydro", "ror", "PHS"}
    ev = json.loads((PV / "POTENTIALS_S4A_EVIDENCE.json").read_text())
    assert all(len(d["sha256"]) == 64 for d in ev["documents"])
    cmp = pd.read_csv(PV / "CANDIDATE_POTENTIAL_VS_MODEL_BY_COUNTRY.csv")
    geo = cmp[(cmp.tech == "geothermal") & (cmp.country == "ID")]
    assert len(geo) == 1 and float(geo.model_p_nom_max_gw.iloc[0]) == 0.0 and float(geo.public_potential_gw.iloc[0]) > 20
