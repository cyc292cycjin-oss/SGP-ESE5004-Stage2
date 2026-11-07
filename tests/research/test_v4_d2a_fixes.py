"""V4 D2a (decision 220; V4_D2A_INSTRUCTION.md section 2): the Fable W08 review fixes.
  F-01  research.demand.v4.id_paper_fuelwood = residue_literal (literal reading of decision 211 item 2; ID 2050 T_v2 +36.89 TWh; its own table folder)
  F-02  the overflow columns of INDUSTRY_2050_SUMMARY_V4.csv and the run_case snapshot are the build rule applied after the conservation layer
  F-05  tests: table overflow = network overflow ledger (built D2a network when present), process_and_feedstock, v4_tables switch-set refusal
  F-06  registry tier / locator of the W08 fragment rows; the m08b convergence record in every table folder
  F-07  BN NEU gas rows: the 2019 base is reduced by the plant's 2019 gas energy use as well
  F-11  anchor_mode != ras with v4 disabled is refused;  F-12  industry curves for any divisor of 8760;  F-14  v4-path potential excludes the rows the build skips
No solver. No network build (the network comparison reads an existing D2a build and is skipped when none is present)."""
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
V4 = ROOT / "research_inputs/industry_v4"
BUILD = Path(os.environ.get("V4_D2A_BUILD", str(ROOT / "results_project/v4d2a/builds/main/integrated/integrated_365_24h_unsolved.nc")))


def _folders():
    return sorted(p for p in V4.glob("out_*") if (p / "V4_SWITCHES.json").exists())


def _potential(s: dict) -> pd.Series:
    """Solid-biomass potential per country as the build takes it (status-filtered rows) for the switch set s."""
    f = ROOT / "research_inputs/biomass_v5" / ("BIOMASS_POTENTIAL_2050_V4.csv" if s["biomass_potential"] == "v4_adjusted" else "BIOMASS_POTENTIAL_2050.csv")
    bp = pd.read_csv(f, keep_default_na=False)
    bp["p"] = pd.to_numeric(bp.potential_main_mwh, errors="coerce").fillna(0.0)
    solid = bp[(bp.feedstock_group != "biogas") & ~bp.status.isin(["DATA_PENDING", "ZERO_BY_DECISION"])]
    return solid.groupby("country").p.sum()


# ---------------------------------------------------------------------------------------------------------------- F-02 / F-14 / F-05 (table side)
def test_f02_table_overflow_is_the_build_rule_after_the_conservation_layer():
    import s2_layers as L
    folders = _folders()
    assert len(folders) >= 3   # out_ras, out_iid, the residue_literal set
    for od in folders:
        rec = json.loads((od / "V4_SWITCHES.json").read_text()); s = rec["switches"]
        S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
        pot = _potential(s)
        for c in S.index:
            cap = float(pot.get(c, 0.0)) * float(s["bio_cap_share"])
            assert abs(float(S.at[c, "solid_biomass_potential_main_mwh"]) - cap) <= 1e-3, (od.name, c, "F-14: table cap = build cap")
            bio, ag = float(S.at[c, "pe_biomass_mwh"]), float(S.at[c, "agriculture_biomass_2050_mwh"])
            cap_tab = float(S.at[c, "solid_biomass_potential_main_mwh"])   # the table's own cap (its summation order differs from the recomputed one by ~1e-5 MWh)
            ov_ind, ov_ag, _, _ = L.biomass_overflow(bio, ag, cap_tab, 1.0, 0.999)   # the build call for bio_cap_share < 1 (cap passed as the potential)
            assert float(S.at[c, "biomass_overflow_industry_mwh"]) == pytest.approx(ov_ind, abs=1e-6), (od.name, c)
            assert float(S.at[c, "biomass_overflow_agriculture_mwh"]) == pytest.approx(ov_ag, abs=1e-6), (od.name, c)
            assert float(S.at[c, "pe_biomass_before_overflow_mwh"]) == float(S.at[c, "pe_biomass_mwh"])
            assert float(S.at[c, "biomass_overflow_industry_to_gas_mwh"]) == 0.0   # useful-heat table
        log = rec["biomass_overflow_recomputed"]
        assert set(log) >= {"VN", "ID", "MY"}
        for c, v in log.items():
            assert v["overflow_industry_mwh"] == pytest.approx(float(S.at[c, "biomass_overflow_industry_mwh"]), abs=1e-6)
        if s["anchor_mode"] == "ras" and s["id_paper_fuelwood"] == "residue":   # Fable F-02: VN main 29.95 -> 41.10 TWh, the pulp-and-paper purchased biomass vector
            vn = log["VN"]
            assert vn["overflow_industry_mwh"] == pytest.approx(41097219.64, abs=1.0) and vn["s30_overflow_industry_mwh"] == pytest.approx(29951239.32, abs=1.0)
            assert vn["overflow_industry_mwh"] - vn["s30_overflow_industry_mwh"] == pytest.approx(11145980.3, abs=1.0)
        if s["anchor_mode"] == "iid" and s["id_paper_fuelwood"] == "residue":
            assert log["VN"]["overflow_industry_mwh"] == pytest.approx(32073767.79, abs=1.0)


def test_f02_snapshot_overflow_matches_the_table():
    for od in _folders():
        snap = json.loads((od / "SNAPSHOT.json").read_text())
        S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
        for c, v in snap["countries"].items():
            if c not in S.index:
                continue
            assert v["overflow"] == pytest.approx(float(S.at[c, "biomass_overflow_industry_mwh"]), abs=1e-6), (od.name, c)
            assert v["overflow_agriculture"] == pytest.approx(float(S.at[c, "biomass_overflow_agriculture_mwh"]), abs=1e-6), (od.name, c)
            assert v["bio_before"] == pytest.approx(float(S.at[c, "pe_biomass_mwh"]), abs=1e-6) and v["pot"] == pytest.approx(float(S.at[c, "solid_biomass_potential_main_mwh"]), abs=1e-6)
            assert v["bio_before"] == pytest.approx(v["T_car"]["biomass"], abs=1e-6)
            assert "overflow_s30" in v and "bio_before_s30" in v


@pytest.mark.skipif(not BUILD.exists(), reason="no built D2a network (results_project/v4d2a/builds/main/integrated/integrated_365_24h_unsolved.nc or V4_D2A_BUILD)")
def test_f05_network_overflow_ledger_equals_the_table():
    import pypsa
    n = pypsa.Network(str(BUILD))
    rec = n.meta["v4_w08"]; od = ROOT / rec["tables_dir"]
    S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
    led = n.meta["s2_demand_ledger"]["industry"]["biomass_overflow"]
    for c, v in led.items():
        if c not in S.index:
            continue
        assert v["overflow_industry_mwh"] == pytest.approx(float(S.at[c, "biomass_overflow_industry_mwh"]), abs=1e-3), c
        assert v["overflow_agriculture_mwh"] == pytest.approx(float(S.at[c, "biomass_overflow_agriculture_mwh"]), abs=1e-3), c
        # the build's dust cleanup (S4L-1) deletes near-zero pools not needed by a fixed demand: MY 793, BN 856, SG 473, TL 664 MWh below the table (Fable F-14)
        assert v["cap_mwh"] == pytest.approx(float(S.at[c, "solid_biomass_potential_main_mwh"]), abs=1.0e3), c
        assert v["industry_biomass_before_mwh"] == pytest.approx(float(S.at[c, "pe_biomass_mwh"]), abs=1e-3), c


# ---------------------------------------------------------------------------------------------------------------- F-05: process_and_feedstock, v4_tables refusal
def test_f05_process_and_feedstock_rule_reproduces_the_committed_tables():
    import v4_outputs as O
    ext = pd.read_csv(O.EDGAR)
    for mode in ("ras", "iid"):
        od = V4 / f"out_{mode}"
        ats = pd.read_csv(od / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False, dtype=str)
        S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
        pr, fc = O.process_and_feedstock(ats, S)
        P0 = pd.read_csv(od / "PROCESS_EMISSIONS_2050_V4.csv"); F0 = pd.read_csv(od / "FEEDSTOCK_CARBON_TERRITORIAL_2050_V4.csv", keep_default_na=False, dtype=str)
        assert len(pr) == len(P0) == 33 and (pr.tco2_2050.to_numpy() == pytest.approx(P0.tco2_2050.to_numpy(), rel=1e-12))
        for col in ("process_2B_2D_2050_t", "territorial_total_2050_t", "full_release_2050_t"):
            assert fc[col].astype(float).to_numpy() == pytest.approx(F0[col].astype(float).to_numpy(), rel=1e-12), col
        mult = ats[ats.sector == "Industry"].groupby("country").multiplier_total.first().astype(float)
        for r in pr.itertuples():   # the rule: 2.A.1 x cement 2050 / 2019 + (minerals - 2.A.1) x multiplier; chemicals / metals x multiplier
            e = ext[ext.iso == r.country]; codes = O.GROUPS[r.group]
            v19 = float(e[e.ipcc_code_2006_for_standard_report.isin(codes)].kt_CO2_2019.sum()) * 1e3
            assert r.tco2_2019 == pytest.approx(v19, rel=1e-12) and r.industry_multiplier == pytest.approx(float(mult[r.country]), rel=1e-12)
            if r.group == "minerals":
                v_cem = float(e[e.ipcc_code_2006_for_standard_report == "2.A.1"].kt_CO2_2019.sum()) * 1e3
                c19, c50 = float(S.at[r.country, "cement_2019_t"]), float(S.at[r.country, "cement_2050_t"])
                want = v_cem * (c50 / c19 if c19 > 0 else 0.0) + (v19 - v_cem) * float(mult[r.country])
            else:
                want = v19 * float(mult[r.country])
            assert r.tco2_2050 == pytest.approx(want, rel=1e-12), (r.country, r.group)


def test_f05_v4_tables_refuses_a_tampered_switch_record(tmp_path):
    from phase4_static import config
    from v4_common import v4_tables
    cfg = config(ROOT, "integrated"); cfg["research"]["demand"]["v4"]["enabled"] = True
    src = V4 / "out_ras"; dst = tmp_path / "research_inputs/industry_v4/out_ras"; shutil.copytree(src, dst)
    assert v4_tables(cfg, tmp_path)["dir"] == dst
    rec = json.loads((dst / "V4_SWITCHES.json").read_text())
    for key, val in (("switch_sha256", "0" * 64), ("dir", "out_iid")):
        bad = dict(rec); bad[key] = val
        (dst / "V4_SWITCHES.json").write_text(json.dumps(bad))
        with pytest.raises(ValueError):
            v4_tables(cfg, tmp_path)
    (dst / "V4_SWITCHES.json").unlink()
    with pytest.raises(FileNotFoundError):
        v4_tables(cfg, tmp_path)


# ---------------------------------------------------------------------------------------------------------------- F-01
def test_f01_residue_literal_switch_value_and_folder():
    from v4_common import SWITCH_VALUES, V4_MAIN, out_name, switch_sha, switches
    assert SWITCH_VALUES["id_paper_fuelwood"] == ("residue", "purchased", "residue_literal")
    s = dict(V4_MAIN, anchor_mode="ras", id_paper_fuelwood="residue_literal")
    name = out_name(s); od = V4 / name
    assert name.startswith("out_ras_") and od.exists(), "the F-01 sensitivity table folder is committed"
    rec = json.loads((od / "V4_SWITCHES.json").read_text())
    assert rec["switch_sha256"] == switch_sha(s) and rec["switches"]["id_paper_fuelwood"] == "residue_literal" and rec["main_set"] is False
    main = json.loads((V4 / "out_ras/V4_SWITCHES.json").read_text())
    d = {c: rec["T_v2_TWh"][c] - main["T_v2_TWh"][c] for c in main["T_v2_TWh"]}
    assert d["ID"] == pytest.approx(36.889854, abs=1e-3)   # Fable SENS_PAPER_FUELWOOD.json: ID 1,483.776362 -> 1,520.666216 TWh (EXACT)
    assert all(abs(v) <= 1e-9 for c, v in d.items() if c != "ID")
    assert rec["asean_T_v2_TWh"] == pytest.approx(3527.227865, abs=1e-5)
    from v4_industry_cache import drop_set, load_cells
    cells = load_cells()
    assert drop_set(cells, s) == drop_set(cells, dict(s, id_paper_fuelwood="residue"))   # both readings drop the paper-row fuelwood record


def test_f01_literal_reading_in_the_chain(tmp_path):
    import v4_industry as V
    from v4_common import V4_MAIN
    I = V.Inputs(); ch = V.Chain(tmp_path / "chain")
    base = V.pack(ch.run(V.final_case(I, dict(V4_MAIN, anchor_mode="ras"))), "main")
    lit = V.pack(ch.run(V.final_case(I, dict(V4_MAIN, anchor_mode="ras", id_paper_fuelwood="residue_literal"))), "literal")
    add_b = [a for a in base["ats_add_info"] if a["country"] == "ID"]; add_l = [a for a in lit["ats_add_info"] if a["country"] == "ID"]
    assert len(add_b) == len(add_l) == 1
    assert add_b[0]["d_mwh"] == pytest.approx(I.idb_main * I.fw["share_non_paper"], rel=1e-12) and add_b[0]["d_mwh"] == pytest.approx(17673285.30, abs=1.0)
    assert add_l[0]["d_mwh"] == pytest.approx(I.fw["mean_mwh"] - I.fw["paper_sdmx_mwh"], rel=1e-12) and add_l[0]["d_mwh"] == pytest.approx(33295597.22, abs=1.0)
    assert (lit["countries"]["ID"]["T"] - base["countries"]["ID"]["T"]) / 1e6 == pytest.approx(36.889854, abs=1e-3)
    for c in base["countries"]:
        if c != "ID":
            assert lit["countries"][c]["T"] == pytest.approx(base["countries"][c]["T"], abs=1e-6)


# ---------------------------------------------------------------------------------------------------------------- F-07
def test_f07_bn_neu_gas_rows_2019_base_deducted():
    import v4_products as P
    from d1_common import NEU_GAS_ACCOUNT
    item = P.bn_neu_methanol_gas()
    assert item["gas_2019_mwh"] == pytest.approx(3451944.44, abs=1.0) and item["gas_2050_mwh"] == pytest.approx(4023950.88, abs=1.0)
    for od in _folders():
        rec = json.loads((od / "V4_SWITCHES.json").read_text())["bn_neu_methanol"]
        ats = pd.read_csv(od / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", dtype=str, keep_default_na=False)
        m = (ats.country == "BN") & (ats.sector == "NonEnergyUse") & (ats.carrier == "gas") & (ats.account == NEU_GAS_ACCOUNT)
        base = pd.to_numeric(ats.loc[m, "base_2019_mwh"]).sum(); v50 = pd.to_numeric(ats.loc[m, "value_2050_mwh"]).sum()
        assert rec["base_2019_before_mwh"] == pytest.approx(5458799.25, abs=0.01) and rec["base_2019_truncated_mwh"] == 0.0
        assert base == pytest.approx(rec["base_2019_before_mwh"] - item["gas_2019_mwh"], rel=1e-9)
        assert v50 == pytest.approx(rec["before_mwh"] - item["gas_2050_mwh"], rel=1e-9)
        assert all("Fable F-07" in g for g in ats.loc[m, "growth_method"])


# ---------------------------------------------------------------------------------------------------------------- F-06
def test_f06_registry_rows_and_convergence_record():
    from v4_common import sha256
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    r = reg.loc["v4_pks_in_mill_share"]
    assert r.tier == "C" and "grade D" in r.description and "tier C" in r.description   # the registry tier scale is A / B / C; the evidence grade D is stated
    r = reg.loc["v4_biomass_overflow_cap_share"]
    assert r.source_locator.startswith("file: configs/research/baseline.yaml") and sha256(ROOT / "configs/research/baseline.yaml") == r.source_sha256
    for od in _folders():
        ev = json.loads((od / "DEMAND_ANCHOR_M08B_EVIDENCE.json").read_text())
        found = []

        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("iterations", "row_error", "column_error"):
                        found.append(path + "/" + k)
                    walk(v, path + "/" + k)
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{path}[{i}]")
        walk(ev)
        assert found, (od.name, "no convergence record (iterations / errors) in DEMAND_ANCHOR_M08B_EVIDENCE.json")
        rec = json.loads((od / "V4_SWITCHES.json").read_text())
        assert rec["files"]["DEMAND_ANCHOR_M08B_EVIDENCE.json"] == sha256(od / "DEMAND_ANCHOR_M08B_EVIDENCE.json")


# ---------------------------------------------------------------------------------------------------------------- F-11, F-12
def test_f11_anchor_mode_with_v4_disabled_is_refused():
    from v4_common import switches
    cfg = {"research": {"demand": {"anchor_mode": "iid", "v4": {"enabled": False}}}}
    with pytest.raises(ValueError):
        switches(cfg)
    assert switches({"research": {"demand": {"anchor_mode": "ras", "v4": {"enabled": False}}}})["enabled"] is False
    assert switches({"research": {"demand": {"anchor_mode": "iid", "v4": {"enabled": True}}}})["anchor_mode"] == "iid"


def test_f12_industry_curves_for_any_divisor_of_the_year(monkeypatch):
    import v4_profiles as PR
    sh = PR.Shapes.__new__(PR.Shapes)
    y = np.arange(8760, dtype=float) + 1.0; y = y / y.mean()
    monkeypatch.setattr(PR, "node_tz", lambda: pd.Series({"X": 7.0}))
    monkeypatch.setattr(sh, "composite", lambda c, tz, et: y)
    assert np.allclose(sh.shape_3h("ID", "X", "elec", 8760), y)
    assert np.allclose(sh.shape_3h("ID", "X", "elec", 2920), y.reshape(2920, 3).mean(1))
    assert np.allclose(sh.shape_3h("ID", "X", "elec", 365), y.reshape(365, 24).mean(1))
    for bad in (1000, 0, 8761):
        with pytest.raises(ValueError):
            sh.shape_3h("ID", "X", "elec", bad)
    assert sh.shape_3h("ID", "Y", "elec", 2920) is None
