"""V5 X20 (decisions 241, 244, 246; X20_SPEC.md + X20_SPEC_ADDENDUM_246.md): switch set of the v5 input revisions.

research.demand.v5 (configs/research/baseline.yaml):
  enabled false (default) = every rule at its 26c2e47d (v4 W14) behaviour, the keys below are ignored (V5_OFF); true = the listed keys,
  missing keys = the v5 main set V5_MAIN. v5 needs research.demand.v4.enabled true (the v5 main set is built on the v4 main set).
  Keys (X20 revision numbers): onwind_calibration (1-1), existing_wind_profile (1-2), existing_solar_profile (Q12), offwind_asean_premium_pct (1-3),
  solar_cap_scale_MY / _ID / _VN and solar_landuse_my (1-4), hydro_inflow_denominator / hydro_inflow_multiplier (1-5), geothermal_cap_id (1-6),
  ph_dc_stock (2-1), ac_dedup (2-2), gas_cap_rule (2-3), neu_gas_growth (2-4), lifetime_boundary / geothermal_existing_lifetime (2-5),
  gem_coord_fix (2-6), distribution_grid (3-4), biomass_residue_fix (1-7).
  Table-level keys (TABLE_KEYS = neu_gas_growth, biomass_residue_fix): they change the v4 table chain (v4_industry.py), so with v5 enabled they enter
  the v4 switch set as v5_<key> (v4_common.switches) and with it the v4 table folder identity: out_<anchor_mode>_v5 = the v4 main set plus the v5 main
  values of both keys, out_<anchor_mode>_<sha12> otherwise. With v5 disabled the v4 switch set has no v5_ key (folder identity of 26c2e47d).
Outside this section (defaults = the 26c2e47d behaviour, no switch-set member): research.s2.co2.storage_potential_case new values (3-1),
research.co2.extra_asean_capacity_mt (3-1), research.cost_scaling.DAC (3-2), research.s2.demand.ev_smart_share (3-3).
The network meta key v5_x20 records the switch set and its SHA256; check_network_meta_v5 refuses a network whose record differs from the configuration.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

V5_OFF = dict(enabled=False, onwind_calibration="ember_country", existing_wind_profile="class0", existing_solar_profile="class0",
              offwind_asean_premium_pct=0.0, solar_cap_scale_MY=1.0, solar_cap_scale_ID=1.0, solar_cap_scale_VN=1.0, solar_landuse_my="lc100",
              hydro_inflow_denominator="all_stock", hydro_inflow_multiplier=1.1, geothermal_cap_id="resource_potential", ph_dc_stock="frozen_base",
              ac_dedup="frozen_base", gas_cap_rule="marketed", neu_gas_growth="industry_multiplier", lifetime_boundary="strict",
              geothermal_existing_lifetime=30, gem_coord_fix="gem", distribution_grid="hv_lossless", biomass_residue_fix="v4")
V5_MAIN = dict(enabled=True, onwind_calibration="gwa_cell_ember", existing_wind_profile="best_class", existing_solar_profile="node_average",
               offwind_asean_premium_pct=0.0, solar_cap_scale_MY=1.0, solar_cap_scale_ID=1.0, solar_cap_scale_VN=1.0, solar_landuse_my="lc100",
               hydro_inflow_denominator="operating_only", hydro_inflow_multiplier=1.1, geothermal_cap_id="reserves_2017", ph_dc_stock="ngcp_tdp",
               ac_dedup="dedup_cables", gas_cap_rule="field_status", neu_gas_growth="product", lifetime_boundary="inclusive",
               geothermal_existing_lifetime=40, gem_coord_fix="verified", distribution_grid="lv_pypsa_eur", biomass_residue_fix="corrected")
TABLE_KEYS = ("neu_gas_growth", "biomass_residue_fix")   # the v5 keys that change the v4 table chain (v4_industry.py): part of the v4 table folder identity
SWITCH_VALUES = dict(onwind_calibration=("ember_country", "gwa_cell_ember"), existing_wind_profile=("class0", "best_class"),
                     existing_solar_profile=("class0", "node_average", "best_class"), solar_landuse_my=("lc100", "open_forest", "oil_palm"),
                     hydro_inflow_denominator=("all_stock", "operating_only"), geothermal_cap_id=("resource_potential", "reserves_2017", "proven_probable"),
                     ph_dc_stock=("frozen_base", "ngcp_tdp"), ac_dedup=("frozen_base", "dedup_only", "dedup_cables"),
                     gas_cap_rule=("marketed", "field_status", "reserve_average"), neu_gas_growth=("industry_multiplier", "product"),
                     lifetime_boundary=("strict", "inclusive"), gem_coord_fix=("gem", "verified"), distribution_grid=("hv_lossless", "lv_pypsa_eur"),
                     biomass_residue_fix=("v4", "corrected"))
NUMERIC = dict(offwind_asean_premium_pct=(0.0, 10.0, 20.0, 30.0), solar_cap_scale_MY=(0.5, 1.0, 2.0), solar_cap_scale_ID=(0.5, 1.0, 2.0),
               solar_cap_scale_VN=(0.5, 1.0, 2.0), hydro_inflow_multiplier=(1.0, 1.1), geothermal_existing_lifetime=(30, 40))


def switches(cfg: dict | None = None, overrides: dict | None = None) -> dict:
    """Effective v5 switch set of the composed configuration (research.demand.v5); overrides (dict) are applied last (tests, scripts)."""
    R = (cfg or {}).get("research") or {}
    d = R.get("demand") or {}
    v = copy.deepcopy(d.get("v5") or {})
    s = dict(V5_MAIN) if v.get("enabled") else dict(V5_OFF)
    if v.get("enabled"):
        s.update(v)
    s.update(overrides or {})
    if s["enabled"] and cfg is not None and not ((d.get("v4") or {}).get("enabled")):
        raise ValueError("research.demand.v5.enabled true needs research.demand.v4.enabled true")
    check(s)
    return s


def check(s: dict) -> None:
    if set(s) != set(V5_OFF):
        raise ValueError(f"research.demand.v5 keys differ from the v5 switch set: extra {sorted(set(s) - set(V5_OFF))}, missing {sorted(set(V5_OFF) - set(s))}")
    for k, allowed in SWITCH_VALUES.items():
        if str(s[k]) not in allowed:
            raise ValueError(f"research.demand.v5.{k} = {s[k]} not in {allowed}")
    for k, allowed in NUMERIC.items():
        if not any(abs(float(s[k]) - a) < 1e-12 for a in allowed):
            raise ValueError(f"research.demand.v5.{k} = {s[k]} not in {allowed}")


def switch_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps({k: s[k] for k in sorted(s)}, sort_keys=True).encode()).hexdigest()


def is_main_set(s: dict) -> bool:
    return set(s) == set(V5_MAIN) and all(s[k] == v for k, v in V5_MAIN.items())


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def record(n, s: dict, tables: dict | None = None, ledgers: dict | None = None, repo: Path | None = None) -> dict:
    """Write n.meta['v5_x20'] (switches, SHA256, input tables with SHA256, per-layer ledger summaries); returns the record."""
    root = repo or ROOT
    files = {k: dict(path=str(p), sha256=sha256(root / p)) for k, p in sorted((tables or {}).items()) if p}
    rec = dict(switches=s, switch_sha256=switch_sha(s), main_set=is_main_set(s), tables=files, ledgers=ledgers or {})
    n.meta["v5_x20"] = rec
    return rec


def in_service(start_year: float, lifetime: float, boundary: str, year: int = 2050) -> bool:
    """V5 X20 (2-5): 2050 in-service rule of an existing unit - strict (S1 / v4): start <= year < start + lifetime; inclusive (v5 main): start + lifetime >= year."""
    s, end = float(start_year), float(start_year) + float(lifetime)
    if boundary not in ("strict", "inclusive"):
        raise ValueError(f"lifetime boundary {boundary}")
    return s <= year and (end >= year if boundary == "inclusive" else end > year)


def s1_geothermal_in_service(survival_json, boundary: str, lifetime: int) -> list:
    """V5 X20 (2-5): S1 geothermal records in service in 2050 under the rule (boundary, lifetime) - re-judged from CommissioningYear for the records S1
    judged by age (SURVIVES_2050 / NOT_ACTIVE_2050); UNRESOLVED_COMMISSIONING and NOT_INHERITED_COMMITTED_OR_PLANNED stay out. With strict / 30 a this is
    exactly the S1 SURVIVES_2050 set (3 records, 186 MW). Shared by s2_layers.geothermal_unit_table (S2 path) and s4a_2_fleet_data.py (GEM path exclusion)."""
    S = json.loads(Path(survival_json).read_text())
    out = []
    for r in S["unit_evidence"]["records"]:
        if r.get("Technology") != "Geothermal" or r.get("SurvivalStatus") not in ("SURVIVES_2050", "NOT_ACTIVE_2050"):
            continue
        if r.get("CommissioningYear") in (None, "") or not in_service(float(r["CommissioningYear"]), lifetime, boundary):
            continue
        out.append(r)
    return out


def check_network_meta_v5(meta: dict, cfg: dict) -> dict:
    """Before export: v5 disabled -> no v5_x20 record; enabled -> the recorded switch SHA256 = the configuration's."""
    s = switches(cfg)
    v = meta.get("v5_x20")
    if not s["enabled"]:
        if v:
            raise ValueError("the network carries a v5_x20 record but research.demand.v5.enabled is false")
        return dict(enabled=False)
    if not v:
        raise ValueError("research.demand.v5.enabled is true but the network meta has no v5_x20 record")
    if v.get("switch_sha256") != switch_sha(s):
        raise ValueError(f"v5 switch SHA256 of the network ({v.get('switch_sha256')}) differs from the configuration ({switch_sha(s)})")
    return dict(enabled=True, switch_sha256=switch_sha(s), main_set=is_main_set(s))


# ---- 4-1 export metadata of a solved network (decision 244; Q11) ---------------------------------------------------------------
BUILD_HISTORY_MOVE = ("interim_notice", "stage", "fullsc_network_complete", "input_coverage_complete", "resource_occupancy_status")   # no read site after the solve
BUILD_HISTORY_COPY = ("skeleton_status", "asset_role", "scientific_results_allowed", "source_is_solved", "asset_qualification")   # read elsewhere: kept in place, copied
STALE_IN_RESEARCH_CONFIG = ("research_config.skeleton_status", "research_config.stage", "research_config.demand.status", "research_config.s2.status",
                            "research_config.site_candidates.*.status")   # not moved: research_config must stay equal to research_config_sha256


def export_meta(n, run: dict, gates: dict, a, repo: Path | None = None) -> dict:
    """V5 X20 4-1: before the solved network is exported (s2_solve, ahead of gate A4): n.meta['run_status'] (termination, the gates computed before the
    export, constraint hooks, authorization, package COMMIT, git HEAD; V6 acceptance V6_PENDING - gates_v6 accept runs after the solve, its result
    goes to the RUN_STATUS.json sidecar, the network is not rewritten) and n.meta['build_history'] (stale build-time keys: moved when nothing reads
    them after the solve, copied otherwise; logs/64_meta_key_reads.log of X20)."""
    import subprocess
    head = None
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo or ROOT), capture_output=True, text=True, check=True).stdout.strip()
    except Exception:   # noqa: BLE001 - outside a git checkout (packages): recorded as None
        pass
    pre = {k: bool(v.get("passed")) for k, v in gates.items() if isinstance(v, dict) and "passed" in v}
    rs = dict(status=run.get("status"), termination_condition=run.get("termination_condition"), objective=run.get("objective"), label=run.get("label"),
              gates_before_export=pre, gates_after_export="RUN_STATUS.json sidecar (B gates, acceptance verdicts)", constraint_hooks=sorted(n.meta.get("required_constraint_hooks", [])),
              authorization=getattr(a, "authorization", None), package_commit=getattr(a, "package_commit", None), git_head=head,
              v6_acceptance="V6_PENDING (gates_v6 accept reads SOLVE_RECEIPT.json after the solve; see V6_ACCEPTANCE.json / RUN_STATUS.json)")
    bh = dict(n.meta.get("build_history") or {})
    moved, copied = {}, {}
    for k in BUILD_HISTORY_MOVE:
        if k in n.meta:
            moved[k] = n.meta.pop(k)
    for k in BUILD_HISTORY_COPY:
        if k in n.meta:
            copied[k] = n.meta[k]
    qd = n.meta.get("qualification_dimensions") or {}
    if isinstance(qd, dict) and "policy_constraint_qualification" in qd:
        moved["qualification_dimensions.policy_constraint_qualification"] = qd.pop("policy_constraint_qualification")
    bh.update(moved_after_solve=moved, copied_after_solve=copied, stale_not_moved=list(STALE_IN_RESEARCH_CONFIG),
              note="build-time status keys of the unsolved network; superseded by run_status (V5 X20 4-1)")
    n.meta["build_history"] = bh; n.meta["run_status"] = rs
    return dict(run_status=rs, moved=sorted(moved), copied=sorted(copied))
