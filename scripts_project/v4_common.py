"""V4 W08 (decisions 203-211; W08_IMPLEMENTATION_SPEC.md): shared paths, switches and constants of the v4 industry / demand layer.

Every v4 change sits behind a switch of research.demand (configs/research/baseline.yaml):
  research.demand.anchor_mode        ras (default; v3.1 fallback with the v3.1 seed; v4 main with the v4 seed, decision 211 item 1) | iid | iib | external
  research.demand.v4.enabled         false (default) = every v3.1 table, byte-identical; true = the build reads the v4 tables of
                                     research_inputs/industry_v4/out_<anchor_mode>/ (written by scripts_project/v4_industry.py)
  research.demand.v4.*               the individual v4 rules (base, residue boundary, (ii) / (i) corrections, products, network layer, curves);
                                     v4_industry.py records the switch set in out_<anchor_mode>/V4_SWITCHES.json and the build refuses a table
                                     set whose switches differ from the configuration.
  research.demand.v4.hvc_basis       V4 D1 (decision 214 items 8 / 9): b (main: 2019 deduction 5.191, 2050 vector 4.627 MWh/t) | a (S2 basis 3.269 / 6.103)
  research.demand.v4.id_paper_fuelwood  residue (main, W08 reading of decision 211 item 2: the paper share of the 2010-2017 fuelwood mean leaves the anchor,
                                     (b) item 17.67 TWh) | residue_literal (V4 D2a, Fable F-01 / decision 220: the 2019 paper-row quantity 41.59 TWh leaves the
                                     2010-2017 mean, (b) item 33.29 TWh; sensitivity, ID 2050 T_v2 +36.89 TWh) | purchased (I2 main)
  research.demand.v4.biomass_potential  v3 (v3.1 table) | v4_adjusted (W08: F3 bagasse R2, F4 in-mill self-use) | v4_adjusted_t04 (V4 D2a, T04: the W08 adjustments plus
                                     the palm-residue basis correction - EFB and fibre energy = wet mass x (1 - moisture) x LHV_dry instead of wet mass x 15 GJ/t,
                                     research_inputs/biomass_v5/PALM_RESIDUE_BASIS_T04.csv; switch alternative) | v4_adjusted_t05 (V4 D2b, decision 221: the energy
                                     basis audit of every category, research_inputs/biomass_v5/BIOMASS_BASIS_T05.csv - T04 plus the categories judged INCONSISTENT there;
                                     since D2c the high-sensitivity switch value of the trunk) | v4_adjusted_t06 (V4 D2c main, decision 223: T05 with the oil palm trunk on
                                     the measured trunk dry mass per palm x LHV_dry, research_inputs/biomass_v5/BIOMASS_BASIS_T06.csv; only the five trunk pools differ)
  research.demand.v4.source_band_basis  V4 D2b (section 3, Fable F-02 side note): source temperature band shares of the fixed industrial biomass (the bands of the
                                     overflow useful heat) - post_product (v4 main: high = cement-kiln biomass / T_v2 biomass after the product vectors, the rest split at
                                     200 C with the s3_0 medium_a_fraction) | s30 (D2a and earlier: the s3_0 shares computed before the product vectors)
  research.demand.v4.lng_regas_adder V4 D2b (section 4.1): asean_tariffs (v4 main: registry v4_lng_regas_adder_asean_tariffs = median of the regulated terminal
                                     tariffs TH / MY / SG / ID) | m08a (v3.1: research.s3.gas.lng_regasification_adder_eur_per_mwh = 1.26). Network build only (s3_layers)
  research.demand.v4.meoh_per_tco2   V4 D2a (decision 220): stoichiometric (v4 main: MWh methanol per t CO2 of the methanolisation link = M_MeOH / M_CO2 x
                                     LHV_MeOH = 4.0248, registry ammonia_methanol_MWh_MeOH_per_tCO2_stoichiometric) | pypsa_eur (v3.1: research.s3.ammonia_methanol
                                     .MWh_MeOH_per_tCO2 = 4.0321). Acts on the network build only (s3_layers); part of the switch set (SHA256, folder).
  research.biomass.missing_cost_rule V4 D1 (decisions 212 item 5, 215 item 5): zero (v3.1: an empty cost of a pool whose registry cost is DATA_PENDING
                                     enters at 0) | proxy (the registry proxy biomass_missing_cost_proxy); null = the value of the switch set (v4.enabled
                                     false -> zero, true -> proxy). It acts on the network build only and is part of the switch set (SHA256, folder).
Table folders (V4 D1, decision 214 item 8): out_<anchor_mode> holds only the v4 main set of that anchor mode (V4_MAIN with that anchor_mode);
V5 X20 (decisions 241, 244, 246): with research.demand.v5.enabled true the table-level v5 keys (v5_common.TABLE_KEYS) join the switch set as
v5_<key>; out_<anchor_mode>_v5 holds the v4 main set plus the v5 main values of those keys (v4_industry.py --set v5_<key>=<value>);
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
           industry_curves="flat", mm_gasoline=False, hvc_basis="b", missing_cost_rule="zero", meoh_per_tco2="pypsa_eur", source_band_basis="s30",
           lng_regas_adder="m08a")
V4_MAIN = dict(enabled=True, base="sdmx_2019", residue_boundary=True, id_paper_fuelwood="residue", household_gasoline="id_to_road", rail_parent="children_only",
               captive_coal=True, products=True, vn_same_run=True, bio_cap_share=0.99, biomass_potential="v4_adjusted_t06", gas_caps="marketed",
               industry_curves="g5_main", mm_gasoline=False, hvc_basis="b", missing_cost_rule="proxy", meoh_per_tco2="stoichiometric", source_band_basis="post_product",
               lng_regas_adder="asean_tariffs")
SWITCH_VALUES = dict(base=("v3_1", "sdmx_2019"), id_paper_fuelwood=("residue", "purchased", "residue_literal"), household_gasoline=("none", "id_to_road"),
                     rail_parent=("in_d1", "children_only"), biomass_potential=("v3", "v4_adjusted", "v4_adjusted_t04", "v4_adjusted_t05", "v4_adjusted_t06"), gas_caps=("gross", "marketed"),
                     industry_curves=("flat", "g5_main", "all_flat"), hvc_basis=("b", "a"), missing_cost_rule=("zero", "proxy"),
                     meoh_per_tco2=("pypsa_eur", "stoichiometric"), source_band_basis=("s30", "post_product"), lng_regas_adder=("m08a", "asean_tariffs"))
MEOH_STOICH_ROW = "ammonia_methanol_MWh_MeOH_per_tCO2_stoichiometric"   # V4 D2a: registry row of the stoichiometric value (v4_d1_registry.py)
LNG_REGAS_ROW = "v4_lng_regas_adder_asean_tariffs"   # V4 D2b (section 4.1): registry row of the ASEAN regulated-tariff regasification adder (v4_d2b_registry.py)
# research.demand.v4.biomass_potential -> potential table of the build (None = the v3.1 table BIOMASS_POTENTIAL_2050.csv)
BIOMASS_POTENTIAL_FILES = {"v3": None, "v4_adjusted": "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv",
                           "v4_adjusted_t04": "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4_T04.csv",   # V4 D2a (T04, decision 220): switch alternative
                           "v4_adjusted_t05": "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4_T05.csv",   # V4 D2b (T05, decision 221): high-sensitivity switch value since D2c
                           "v4_adjusted_t06": "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4_T06.csv"}   # V4 D2c (T06, decision 223): v4 main
BIOMASS_POTENTIAL_V5FIX = "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4_T06_V5FIX.csv"   # V5 X20 (1-7): T06 on the corrected residue chain


def biomass_potential_file(s: dict) -> str | None:
    """Potential table of the switch set: V5 X20 v5_biomass_residue_fix = corrected -> T06 on the corrected d1_biomass chain (needs v4_adjusted_t06);
    otherwise BIOMASS_POTENTIAL_FILES[biomass_potential]."""
    if s.get("v5_biomass_residue_fix") == "corrected":
        return BIOMASS_POTENTIAL_V5FIX
    return BIOMASS_POTENTIAL_FILES[s["biomass_potential"]]


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
    if (d.get("v5") or {}).get("enabled"):   # V5 X20 (decisions 241, 244, 246): the table-level v5 keys join the v4 switch set (v5_common.TABLE_KEYS)
        import v5_common as V5
        s5 = V5.switches(cfg)   # raises when research.demand.v4.enabled is false
        s.update({f"v5_{k}": s5[k] for k in V5.TABLE_KEYS})
    s.update(overrides or {})
    check(s)
    return s


def is_main_set(s: dict) -> bool:
    """True when s is the v4 main set V4_MAIN of its anchor mode (no other key, every value equal)."""
    return set(s) == set(V4_MAIN) | {"anchor_mode"} and all(s[k] == v for k, v in V4_MAIN.items())


def v5_table_keys(s: dict) -> list:
    """V5 X20: the v5_<key> members of a v4 switch set (empty with research.demand.v5.enabled false)."""
    return sorted(k for k in s if k.startswith("v5_"))


def is_v5_main_tables(s: dict) -> bool:
    """V5 X20: True when s is the v4 main set plus the v5 main values of every table-level v5 key (folder out_<anchor_mode>_v5)."""
    import v5_common as V5
    want = {f"v5_{k}" for k in V5.TABLE_KEYS}
    return (set(s) == set(V4_MAIN) | {"anchor_mode"} | want and all(s[k] == v for k, v in V4_MAIN.items())
            and all(s[f"v5_{k}"] == V5.V5_MAIN[k] for k in V5.TABLE_KEYS))


def out_name(s: dict) -> str:
    """Table folder name: out_<anchor_mode> for the v4 main set of that anchor mode, out_<anchor_mode>_v5 for the v4 main set plus the v5 main table keys
    (V5 X20), out_<anchor_mode>_<switch SHA256[:12]> otherwise (V4 D1)."""
    if is_main_set(s):
        return f"out_{s['anchor_mode']}"
    if v5_table_keys(s) and is_v5_main_tables(s):
        return f"out_{s['anchor_mode']}_v5"
    return f"out_{s['anchor_mode']}_{switch_sha(s)[:12]}"


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
                biomass_potential=biomass_potential_file(s),
                gas_caps=("research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv" if s["gas_caps"] == "marketed" else None))


def check(s: dict) -> None:
    if s["anchor_mode"] not in ANCHOR_MODES:
        raise ValueError(f"research.demand.anchor_mode {s['anchor_mode']} not in {ANCHOR_MODES}")
    if not s["enabled"] and s["anchor_mode"] != "ras":   # V4 D2a (Fable F-11): with v4 disabled the anchor mode would be silently inert
        raise ValueError(f"research.demand.anchor_mode {s['anchor_mode']} needs research.demand.v4.enabled true (with v4 disabled the v3.1 tables are read and the mode is inert)")
    for k, allowed in SWITCH_VALUES.items():
        if str(s.get(k)) not in allowed:
            raise ValueError(f"research.demand.v4.{k} = {s.get(k)} not in {allowed}")
    if not 0.0 < float(s["bio_cap_share"]) <= 1.0:
        raise ValueError("research.demand.v4.bio_cap_share must be in (0, 1]")
    v5k = v5_table_keys(s)
    if v5k:   # V5 X20: all table-level v5 keys or none, only on the v4 switch set
        import v5_common as V5
        want = sorted(f"v5_{k}" for k in V5.TABLE_KEYS)
        if v5k != want:
            raise ValueError(f"v5 table keys {v5k} differ from {want}")
        if not s["enabled"]:
            raise ValueError("v5 table keys need research.demand.v4.enabled true")
        for k in V5.TABLE_KEYS:
            if str(s[f"v5_{k}"]) not in V5.SWITCH_VALUES[k]:
                raise ValueError(f"research.demand.v5.{k} = {s[f'v5_{k}']} not in {V5.SWITCH_VALUES[k]}")
        if s["v5_biomass_residue_fix"] == "corrected" and s["biomass_potential"] != "v4_adjusted_t06":
            raise ValueError("research.demand.v5.biomass_residue_fix corrected is implemented on research.demand.v4.biomass_potential v4_adjusted_t06 only")


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


def overflow_split(biomass_mwh: float, agriculture_mwh: float, cap_mwh: float) -> tuple[float, float]:
    """V4 D2a (Fable F-02, decision 220): fixed solid-biomass demand above the cap (cap = bio_cap_share x potential), industry first, then agriculture -
    the s3_0_industry.py / s2_layers.biomass_overflow rule applied to the conservation-layer biomass (T_v2 biomass incl. the product vectors)."""
    overflow = max(0.0, float(biomass_mwh) + float(agriculture_mwh) - float(cap_mwh))
    ov_ind = min(overflow, float(biomass_mwh))
    return ov_ind, min(overflow - ov_ind, float(agriculture_mwh))


SOURCE_BAND_MIN_MWH = 1.0   # V4 D2b: below 1 MWh of fixed industrial biomass the source band shares stay the s3_0 shares


def source_band_shares(cement_biomass_mwh: float, biomass_mwh: float, medium_a_fraction: float) -> dict:
    """V4 D2b (section 3, Fable F-02 side note; research.demand.v4.source_band_basis = post_product): source band shares of the fixed industrial biomass
    after the product vectors - the s3_0_industry.py rule (high = cement-kiln biomass / fixed biomass, medium = the rest, split at 200 C with
    medium_a_fraction) applied to the conservation-layer biomass (T_v2 biomass incl. the purchased biomass of the product vectors, which is medium-band
    steam / drying use). Returns None when the fixed biomass is below SOURCE_BAND_MIN_MWH (numerical dust, e.g. BN 3.5e-8 MWh in the dispersed row): the
    s3_0 shares are kept (they act on an overflow of 0)."""
    bio = float(biomass_mwh)
    if bio < SOURCE_BAND_MIN_MWH:
        return None
    hi = min(1.0, max(0.0, float(cement_biomass_mwh)) / bio)
    med = 1.0 - hi
    f = float(medium_a_fraction)
    return {"medium_a": med * f, "medium_b": med * (1.0 - f), "high": hi}


def meoh_per_tco2_value(cfg: dict, repo: Path | None = None) -> tuple[float, str]:
    """V4 D2a (decision 220): MWh methanol per t CO2 of the methanolisation link for the configured switch set - pypsa_eur: the configured
    research.s3.ammonia_methanol.MWh_MeOH_per_tCO2 (v3.1, 4.0321); stoichiometric: the registry row MEOH_STOICH_ROW (CO2 + 3 H2 -> CH3OH + H2O,
    M_MeOH / M_CO2 x LHV_MeOH = 4.0248). Returns (value, basis)."""
    A = cfg["research"]["s3"]["ammonia_methanol"]
    s = switches(cfg)
    if s["meoh_per_tco2"] == "pypsa_eur":
        return float(A["MWh_MeOH_per_tCO2"]), "pypsa_eur: research.s3.ammonia_methanol.MWh_MeOH_per_tCO2"
    import pandas as pd
    reg = pd.read_csv((repo or ROOT) / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    if MEOH_STOICH_ROW not in reg.index:
        raise KeyError(f"registry row {MEOH_STOICH_ROW} missing (scripts_project/v4_d1_registry.py)")
    return float(reg.at[MEOH_STOICH_ROW, "value"]), f"stoichiometric: registry {MEOH_STOICH_ROW}"


def lng_regas_adder_value(cfg: dict, repo: Path | None = None) -> tuple[float, str]:
    """V4 D2b (section 4.1): LNG regasification adder on the LNG import marginal cost (EUR2020/MWh) for the configured switch set - m08a: the configured
    research.s3.gas.lng_regasification_adder_eur_per_mwh (v3.1, 1.26 = 0.5 USD2024/MMBtu, Argus / IGU secondary); asean_tariffs: the registry row LNG_REGAS_ROW
    (median of the published regulated terminal tariffs of TH / MY / SG / ID at full utilisation, EUR2020/MWh). Returns (value, basis)."""
    s = switches(cfg)
    if s["lng_regas_adder"] == "m08a":
        return float(cfg["research"]["s3"]["gas"].get("lng_regasification_adder_eur_per_mwh", 0.0)), "m08a: research.s3.gas.lng_regasification_adder_eur_per_mwh"
    import pandas as pd
    reg = pd.read_csv((repo or ROOT) / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    if LNG_REGAS_ROW not in reg.index:
        raise KeyError(f"registry row {LNG_REGAS_ROW} missing (scripts_project/v4_d2b_registry.py)")
    return float(reg.at[LNG_REGAS_ROW, "value"]), f"asean_tariffs: registry {LNG_REGAS_ROW}"


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
