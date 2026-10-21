"""M08a A7 (decisions 132, 133): scenario / coalition / finance variants generated deterministically from a built base network.

    PYTHONHASHSEED=0 python scripts_project/m08a_variants.py --repo . --base <dir>/<scenario>_2920_3h_unsolved.nc --out <dir> \
        --set cross_border.stock_mode=keep_stock_no_new --set disconnected.co2_shipping_intra_asean=forbid \
        --set coalition.remove_countries=[VN] --set finance.wacc_mode=country_specific

One script for every variant, so that the cloud can derive them from the uploaded base networks (input and output SHA256 in
<out>/<name>_VARIANT_RECEIPT.json). The base must have been built by scripts_project/s2_network.py with the CURRENT config
(its research_config_sha256 is re-derived from the config files + its recorded overrides; --allow-stale-base only for
evidence runs, recorded in the receipt). Order of application (fixed): coalition.remove_countries -> cross_border.stock_mode
-> disconnected.co2_shipping_intra_asean -> finance.wacc_mode. keep_stock_no_new needs an integrated base and yields a
disconnected-scenario network; co2_shipping forbid needs a disconnected network. Nothing is solved.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from m08a_layers import (VARIANT_DEFAULTS, apply_co2_shipping, apply_remove_countries, apply_stock_mode, variant_values)   # noqa: E402

SCRIPT = "scripts_project/m08a_variants.py"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_set(s: str):
    key, val = s.split("=", 1)
    if key not in VARIANT_DEFAULTS:
        raise KeyError(f"--set accepts only the variant keys {sorted(VARIANT_DEFAULTS)}, got {key}")
    import yaml
    v = yaml.safe_load(val)
    if key == "coalition.remove_countries":
        v = sorted(v or [])
    return key, v


def apply_overrides(R: dict, overrides: list) -> dict:
    """Same parsing rule as scripts_project/s2_network.py build_scenario_s2 (bool accepts on/off; list / dict / null via YAML)."""
    import yaml
    for ov in overrides:
        key, val = ov.split("=", 1); d = R; parts = key.split(".")
        for k in parts[:-1]:
            d = d.setdefault(k, {})
        old = d.get(parts[-1])
        if isinstance(old, bool):
            d[parts[-1]] = val.lower() in ("1", "true", "yes", "on")
        elif old is None or isinstance(old, (list, dict)):
            d[parts[-1]] = yaml.safe_load(val)
        else:
            d[parts[-1]] = type(old)(val)
    return R


def composed_config(repo: Path, scenario: str, overrides: list) -> dict:
    from phase4_static import config
    cfg = config(repo, scenario)
    R = apply_overrides(cfg["research"], list(overrides))
    R["config_overrides"] = list(overrides)
    return cfg


def variant_name(base_scenario: str, sets: dict) -> str:
    tag = []
    if sets.get("cross_border.stock_mode") == "keep_stock_no_new":
        tag.append("keepstock")
    if sets.get("disconnected.co2_shipping_intra_asean") == "forbid":
        tag.append("noco2ship")
    if sets.get("coalition.remove_countries"):
        tag.append("minus" + "".join(sets["coalition.remove_countries"]))
    if sets.get("finance.wacc_mode") == "country_specific":
        tag.append("wacccountry")
    scen = "disconnected" if sets.get("cross_border.stock_mode") == "keep_stock_no_new" else base_scenario
    return scen + ("_" + "_".join(tag) if tag else "")


def derive(repo: Path, base: Path, out: Path, sets: dict, costs_path: Path | None = None, allow_stale_base: bool = False) -> dict:
    import pypsa
    from network_checks import compare_roundtrip
    from scenario_network import config_sha, jsonable
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise SystemExit("run with PYTHONHASHSEED=0 (deterministic NetCDF export)")
    repo, base, out = Path(repo).resolve(), Path(base).resolve(), Path(out); out.mkdir(parents=True, exist_ok=True)
    base_sha = sha(base)
    n = pypsa.Network(str(base))
    bR = n.meta.get("research_config") or {}
    base_scen = str(n.meta.get("scenario") or bR.get("scenario"))
    base_ov = list(bR.get("config_overrides") or [])
    if variant_values(bR) != VARIANT_DEFAULTS | {"coalition.remove_countries": []}:
        raise ValueError("the base network is itself a variant; derive variants from a network built by s2_network.py")
    expected = config_sha(composed_config(repo, base_scen, base_ov)["research"])
    stale = expected != n.meta.get("research_config_sha256")
    if stale and not allow_stale_base:
        raise SystemExit(f"base network {base.name} was built with another config (research_config_sha256 differs); rebuild it or pass --allow-stale-base for evidence")
    sets = {k: sets[k] for k in VARIANT_DEFAULTS if k in sets and sets[k] != VARIANT_DEFAULTS[k]}
    out_scen = "disconnected" if sets.get("cross_border.stock_mode") == "keep_stock_no_new" else base_scen
    if sets.get("cross_border.stock_mode") == "keep_stock_no_new" and base_scen != "integrated":
        raise ValueError("cross_border.stock_mode keep_stock_no_new derives from an integrated base network")
    var_ov = [f"{k}={json.dumps(v) if isinstance(v, list) else v}" for k, v in sets.items()]
    cfg = composed_config(repo, out_scen, base_ov + var_ov)
    R = cfg["research"]
    led = {}
    led["coalition"] = apply_remove_countries(n, sets.get("coalition.remove_countries", []))
    n.meta["scenario"] = out_scen
    led["stock_mode"] = apply_stock_mode(n, sets.get("cross_border.stock_mode", "remove_all")) if out_scen == "disconnected" else dict(mode="remove_all", note="integrated network: not applicable")
    led["co2_shipping"] = apply_co2_shipping(n, sets.get("disconnected.co2_shipping_intra_asean", "allow"))
    if sets.get("finance.wacc_mode") == "country_specific":
        from s4c_layers import apply_wacc_mode
        costs_path = Path(costs_path) if costs_path else base.parent / "costs_active_research.csv"
        costs = pd.read_csv(costs_path, index_col=0)
        led["finance"] = {k: v for k, v in apply_wacc_mode(n, costs, cfg, repo).items() if k != "rates_by_carrier"}
        led["finance"]["costs_table"] = dict(path=str(costs_path), sha256=sha(costs_path))
    else:
        led["finance"] = dict(mode="uniform")
    if out_scen != base_scen:   # keep_stock_no_new: the disconnected identity with the stock kept
        sw = R["cross_border"]
        n.meta["research_cross_border"] = dict(switches={k: bool(v) for k, v in sw.items()}, ledger=dict(stock_mode=led["stock_mode"]))
    name = variant_name(base_scen, sets)
    res = "365_24h" if "365_24h" in base.name else "2920_3h"
    n.meta.update(**jsonable(dict(research_config=R, research_config_sha256=config_sha(R), research_variant=dict(
        script=SCRIPT, script_sha256=sha(repo / SCRIPT), layers_sha256=sha(repo / "scripts_project/m08a_layers.py"), base=dict(file=base.name, sha256=base_sha, scenario=base_scen),
        sets=sets, overrides=var_ov, stale_base_allowed=bool(stale), ledgers=led, solver_runs=0))))
    if "research_variant" in n.meta:
        n.meta["research_variant"] = jsonable(n.meta["research_variant"])
    try:   # A8: configuration-subset hash of GATES_V6 G2.2 (written when gates_v6 is available)
        from v5.gates_v6 import config_subset_sha256
        n.meta["research_config_subset_sha256"] = config_subset_sha256(R)
    except ImportError:
        pass
    path = out / f"{name}_{res}_unsolved.nc"
    n.export_to_netcdf(path)
    back = pypsa.Network(str(path)); compare_roundtrip(n, back)
    receipt = dict(status="M08A_VARIANT_BUILT", script=SCRIPT, base=dict(path=str(base), sha256=base_sha, scenario=base_scen, stale_config=bool(stale)),
                   output=dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size, scenario=out_scen,
                               components={c.name: int(len(c.df)) for c in n.iterate_components()}),
                   sets=sets, overrides=base_ov + var_ov, research_config_sha256=n.meta["research_config_sha256"],
                   research_config_subset_sha256=n.meta.get("research_config_subset_sha256"), ledgers=jsonable(led), solver_runs=0)
    (out / f"{name}_{res}_VARIANT_RECEIPT.json").write_text(json.dumps(receipt, indent=1, sort_keys=True, default=str) + "\n")
    return receipt


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=HERE.parent); p.add_argument("--base", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    p.add_argument("--set", action="append", default=[], help="variant key=value (cross_border.stock_mode, disconnected.co2_shipping_intra_asean, coalition.remove_countries, finance.wacc_mode)")
    p.add_argument("--costs", type=Path, default=None, help="costs_active_research.csv of the base build (wacc_mode country_specific); default next to the base")
    p.add_argument("--allow-stale-base", action="store_true", help="evidence only: accept a base built with another config (recorded)")
    a = p.parse_args()
    sets = dict(parse_set(s) for s in a.set)
    r = derive(a.repo, a.base, a.out, sets, a.costs, a.allow_stale_base)
    print(json.dumps(dict(output=r["output"]["path"], sha256=r["output"]["sha256"], scenario=r["output"]["scenario"], sets=r["sets"]), indent=1))


if __name__ == "__main__":
    main()
