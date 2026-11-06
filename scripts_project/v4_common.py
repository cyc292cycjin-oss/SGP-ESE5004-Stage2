"""V4 W08 (decisions 203-211; W08_IMPLEMENTATION_SPEC.md): shared paths, switches and constants of the v4 industry / demand layer.

Every v4 change sits behind a switch of research.demand (configs/research/baseline.yaml):
  research.demand.anchor_mode        ras (default; v3.1 fallback with the v3.1 seed; v4 main with the v4 seed, decision 211 item 1) | iid | iib | external
  research.demand.v4.enabled         false (default) = every v3.1 table, byte-identical; true = the build reads the v4 tables of
                                     research_inputs/industry_v4/out_<anchor_mode>/ (written by scripts_project/v4_industry.py)
  research.demand.v4.*               the individual v4 rules (base, residue boundary, (ii) / (i) corrections, products, network layer, curves);
                                     v4_industry.py records the switch set in out_<anchor_mode>/V4_SWITCHES.json and the build refuses a table
                                     set whose switches differ from the configuration.
  research.demand.v4.hvc_basis       V4 D1 (decision 214 items 8 / 9): b (main: 2019 deduction 5.191, 2050 vector 4.627 MWh/t) | a (S2 basis 3.269 / 6.103)
  research.biomass.missing_cost_rule V4 D1 (decisions 212 item 5, 215 item 5): zero (v3.1: an empty cost of a pool whose registry cost is DATA_PENDING
                                     enters at 0) | proxy (the registry proxy biomass_missing_cost_proxy); null = the value of the switch set (v4.enabled
                                     false -> zero, true -> proxy). It acts on the network build only and is part of the switch set (SHA256, folder).
Table folders (V4 D1, decision 214 item 8): out_<anchor_mode> holds only the v4 main set of that anchor mode (V4_MAIN with that anchor_mode);
every other switch set is written to out_<anchor_mode>_<first 12 hex of its switch SHA256>; every folder carries V4_SWITCHES.json, and the build
(s2_network.py, m08a_variants.py) checks that the switch SHA256 in the network meta = the folder's = the configuration's (check_network_meta).
Nothing here solves or builds a network.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4_DIR = ROOT / "research_inputs" / "industry_v4"
SRC = ROOT / "research_inputs" / "assembly_v1" / "sources"
SDMX_DIR = SRC / "unsd_sdmx_2019"
DEMAND_DIR = ROOT / "research_inputs" / "demand_v5"
BIOMASS_DIR = ROOT / "research_inputs" / "biomass_v5"
IND_V3 = ROOT / "research_inputs" / "industry_v3"
REG_DIR = ROOT / "research_inputs" / "registry_v5"

ASEAN = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
ASEAN10 = [c for c in ASEAN if c != "TL"]
SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")
FUELS = ("coal", "oil", "gas", "biomass")
FOSSIL = ("coal", "oil", "gas")
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
ANCHOR_MODES = ("ras", "iid", "iib", "external")

# switch defaults = v3.1 (every v4 rule off); the v4 main set (decision 211) is V4_MAIN
V31 = dict(enabled=False, base="v3_1", residue_boundary=False, id_paper_fuelwood="purchased", household_gasoline="none", rail_parent="in_d1",
           captive_coal=False, products=False, vn_same_run=False, bio_cap_share=1.0, biomass_potential="v3", gas_caps="gross",
           industry_curves="flat", mm_gasoline=False, hvc_basis="b", missing_cost_rule="zero")
V4_MAIN = dict(enabled=True, base="sdmx_2019", residue_boundary=True, id_paper_fuelwood="residue", household_gasoline="id_to_road", rail_parent="children_only",
               captive_coal=True, products=True, vn_same_run=True, bio_cap_share=0.99, biomass_potential="v4_adjusted", gas_caps="marketed",
               industry_curves="g5_main", mm_gasoline=False, hvc_basis="b", missing_cost_rule="proxy")
SWITCH_VALUES = dict(base=("v3_1", "sdmx_2019"), id_paper_fuelwood=("residue", "purchased"), household_gasoline=("none", "id_to_road"),
                     rail_parent=("in_d1", "children_only"), biomass_potential=("v3", "v4_adjusted"), gas_caps=("gross", "marketed"),
                     industry_curves=("flat", "g5_main", "all_flat"), hvc_basis=("b", "a"), missing_cost_rule=("zero", "proxy"))


def switches(cfg: dict | None = None, overrides: dict | None = None) -> dict:
    """Effective switch set from research.demand.anchor_mode + research.demand.v4 (+ research.biomass.missing_cost_rule) of the composed configuration:
    v4.enabled false -> every rule at its v3.1 value (the other v4 keys are ignored); v4.enabled true -> the listed v4 keys (missing keys = the v4
    main set V4_MAIN). research.biomass.missing_cost_rule, when not null, overrides the switch-set value in both cases (V4 D1)."""
    R = (cfg or {}).get("research") or {}
    d = R.get("demand") or {}
    v = copy.deepcopy(d.get("v4") or {})
    if v.get("enabled"):
        s = dict(V4_MAIN); s.update(v)
    else:
        s = dict(V31)
    s["anchor_mode"] = str(d.get("anchor_mode", "ras"))
    mc = (R.get("biomass") or {}).get("missing_cost_rule")
    if mc is not None:
        s["missing_cost_rule"] = str(mc)
    s.update(overrides or {})
    check(s)
    return s


def is_main_set(s: dict) -> bool:
    """True when s is the v4 main set V4_MAIN of its anchor mode (no other key, every value equal)."""
    return set(s) == set(V4_MAIN) | {"anchor_mode"} and all(s[k] == v for k, v in V4_MAIN.items())


def out_name(s: dict) -> str:
    """Table folder name: out_<anchor_mode> for the v4 main set of that anchor mode, out_<anchor_mode>_<switch SHA256[:12]> otherwise (V4 D1)."""
    return f"out_{s['anchor_mode']}" if is_main_set(s) else f"out_{s['anchor_mode']}_{switch_sha(s)[:12]}"


def v4_tables(cfg: dict, repo: Path | None = None) -> dict | None:
    """Network-facing v4 tables of the configured switch set (None when research.demand.v4.enabled is false). The folder (out_name) and its
    V4_SWITCHES.json must carry the same switch set (SHA256), otherwise the build stops: regenerate with scripts_project/v4_industry.py."""
    s = switches(cfg)
    if not s["enabled"]:
        return None
    od = (repo or ROOT) / "research_inputs" / "industry_v4" / out_name(s)
    if not (od / "V4_SWITCHES.json").exists():
        raise FileNotFoundError(f"no v4 table folder {od.name} for the switch set {s}: run scripts_project/v4_industry.py --anchor-mode {s['anchor_mode']} with the "
                                "--set overrides of this set")
    rec = json.loads((od / "V4_SWITCHES.json").read_text())
    if rec["switch_sha256"] != switch_sha(s) or rec.get("dir", od.name) != od.name:
        raise ValueError(f"v4 tables in {od} were written for another switch set ({rec['switches']}) than the configuration ({s}): rerun v4_industry.py")
    rel = lambda n: str((od / n).relative_to(repo or ROOT))   # noqa: E731
    return dict(dir=od, switches=s, record=rec, demand_table=rel("DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"), anchor_table=rel("DEMAND_ANCHOR_AEO8_ATS.csv"),
                summary_table=rel("INDUSTRY_2050_SUMMARY_V4.csv"), carrier_node_shares=rel("INDUSTRY_CARRIER_NODE_SHARES_V4.csv"),
                feedstock_table=rel("FEEDSTOCK_CARBON_TERRITORIAL_2050_V4.csv"), process_table=rel("PROCESS_EMISSIONS_2050_V4.csv"),
                curve_weights=rel("INDUSTRY_CURVE_WEIGHTS_V4.csv"),
                biomass_potential=("research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv" if s["biomass_potential"] == "v4_adjusted" else None),
                gas_caps=("research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv" if s["gas_caps"] == "marketed" else None))


def check(s: dict) -> None:
    if s["anchor_mode"] not in ANCHOR_MODES:
        raise ValueError(f"research.demand.anchor_mode {s['anchor_mode']} not in {ANCHOR_MODES}")
    for k, allowed in SWITCH_VALUES.items():
        if str(s.get(k)) not in allowed:
            raise ValueError(f"research.demand.v4.{k} = {s.get(k)} not in {allowed}")
    if not 0.0 < float(s["bio_cap_share"]) <= 1.0:
        raise ValueError("research.demand.v4.bio_cap_share must be in (0, 1]")


def out_dir(s: dict) -> Path:
    return V4_DIR / out_name(s)


def check_network_meta(meta: dict, cfg: dict, repo: Path | None = None) -> dict:
    """V4 D1 (decision 214 item 8): before a network is written, the switch SHA256 recorded in its meta (v4_w08, and the demand ledger's copy) must
    equal the configuration's and that of the table folder's V4_SWITCHES.json, the recorded folder must be out_name(switches), and the recorded file
    hashes must be the folder's; a network without v4 tables must not carry a v4 record. Raises ValueError otherwise; returns the checked values."""
    root = repo or ROOT
    s = switches(cfg)
    v = meta.get("v4_w08")
    led = ((((meta.get("s2_demand_ledger") or {}).get("industry")) or {}).get("v4_w08"))
    if not s["enabled"]:
        if v or led:
            raise ValueError("the network carries a v4 table record but research.demand.v4.enabled is false")
        return dict(enabled=False, missing_cost_rule=s["missing_cost_rule"])
    if not v:
        raise ValueError("research.demand.v4.enabled is true but the network meta has no v4_w08 record")
    od = root / "research_inputs" / "industry_v4" / out_name(s)
    rec = json.loads((od / "V4_SWITCHES.json").read_text())
    want = switch_sha(s)
    got = dict(config=want, folder=rec["switch_sha256"], network=v.get("switch_sha256"), demand_ledger=(led or {}).get("switch_sha256", want))
    if len(set(got.values())) != 1:
        raise ValueError(f"switch SHA256 differ between configuration, table folder and network meta: {got}")
    rel = str(od.relative_to(root))
    if v.get("tables_dir") != rel or (led and led.get("tables_dir") != rel):
        raise ValueError(f"network meta records the table folder {v.get('tables_dir')} / {(led or {}).get('tables_dir')}, the switch set needs {rel}")
    if v.get("files") != rec["files"]:
        raise ValueError(f"file hashes recorded in the network differ from {rel}/V4_SWITCHES.json")
    return dict(enabled=True, switch_sha256=want, tables_dir=rel, main_set=is_main_set(s), missing_cost_rule=s["missing_cost_rule"])


def switch_sha(s: dict) -> str:
    return hashlib.sha256(json.dumps({k: s[k] for k in sorted(s)}, sort_keys=True).encode()).hexdigest()


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_config(repo: Path | None = None, scenario: str = "baseline") -> dict:
    import sys
    sp = str((repo or ROOT) / "scripts_project")
    if sp not in sys.path:
        sys.path.insert(0, sp)
    from phase4_static import config
    return config(repo or ROOT, scenario)
