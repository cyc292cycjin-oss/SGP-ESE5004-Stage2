"""V3 HPC package step 2 (instruction V14 section 2; V3_RULES.md section 12.3, written before the builds): rebuild check of F1-F4, read-only, no solver.
  F1 / F2 against the registered decision-180 networks (1bddacb7 / b262f6aa): only links_marginal_cost and links_efficiency of the 810 ship links, at the S-A
  values with eta 1; meta only the ship-cost keys, the two config hashes, the build-worktree path (+ the variant base SHA256 of F2 = new F1);
  F3 / F4 against F1 / F2: only stores_e_nom of the 96 EV batteries and links_p_nom of the 96 BEV chargers, bit-wise 0.5 x; meta only the fleet keys,
  the override record, the two config hashes (+ the variant base SHA256 of F4 = F3);
  F2 - F1 and F4 - F3: the same difference structure as the registered pair, with the counts of review dimension 4.
usage: python chk_f.py <builds_op> <v3hpc builds> <worktree> <evidence dir>"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pypsa

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chk_nets import compare  # noqa: E402

REG_DIR, NEW, W, EV = map(Path, sys.argv[1:5]); EV.mkdir(parents=True, exist_ok=True)
REG = {"F1": ("integrated/integrated_2920_3h_unsolved.nc", "1bddacb7c5d6b70df11a6f038001f291ff92a926b60610b30a27d2fe975853f8"),
       "F2": ("no_new_xb/no_new_xb_2920_3h_unsolved.nc", "b262f6aa76356e1bda20893ae324d5e3e351154b12b9fb2b951877dd469723c8")}
FILES = {"F1": NEW / "sa/integrated/integrated_2920_3h_unsolved.nc", "F2": NEW / "sa/no_new_xb/no_new_xb_2920_3h_unsolved.nc",
         "F3": NEW / "sa_ev05/integrated/integrated_2920_3h_unsolved.nc", "F4": NEW / "sa_ev05/no_new_xb/no_new_xb_2920_3h_unsolved.nc"}
SHIP = ("oil non-fossil ship", "methanol ship", "ammonia ship")
META_SHIP = {"research_config.liquids.ship_cost_basis", "research_config_sha256", "research_config_subset_sha256", "s2_layers.geothermal.bus_mapping_source.path"} | \
            {f"{k}.{x}" for k in ("research_liquids", "v3_layers.liquids") for x in ("ship_cost_basis", "cost_range_eur_per_mwh", "efficiency_range")}
META_EV = {"research_config.s2.demand.ev_fleet_scale", "research_config.config_overrides", "research_config_sha256", "research_config_subset_sha256"} | \
          {f"{k}.{x}" for k in ("research_ev", "v3_layers.ev") for x in ("fleet_scale", "fleet_equivalent_vehicles", "battery_mwh_total", "charger_mw_total")}
reg = pd.read_csv(W / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
rv = lambda p: float(reg.loc[p, "value"])
res = dict(script="chk_f.py", rules="V3_RULES.md section 12.3 (written before the builds)", comparisons={}, problems=[])


def plain(r):   # a comparison without differences outside the listed variables / meta keys, no index change, no attribute change
    return not r["only_in_old"] and not r["only_in_new"] and not r["index_changes"] and not r["attributes"]


def judge(label, r, allowed_vars, allowed_meta, extra_ok=True, notes=None):
    vars_ = {k: v for k, v in r["variables"].items() if v.get("n_differing", 1) != 0}
    ok = plain(r) and set(vars_) <= set(allowed_vars) and set(r["meta_keys"]) <= set(allowed_meta) and extra_ok
    res["comparisons"][label] = dict(passed=bool(ok), sha256_old=r["sha256_old"], sha256_new=r["sha256_new"], bytes_new=r["bytes_new"],
                                     differing_variables={k: dict(n=v.get("n_differing"), carriers=v.get("differing_carriers")) for k, v in vars_.items()},
                                     differing_meta_keys=r["meta_keys"], index_changes={k: (len(v["removed"]), len(v["added"])) for k, v in r["index_changes"].items()},
                                     only_in_old=r["only_in_old"], only_in_new=r["only_in_new"], attributes=r["attributes"], notes=notes or {})
    if not ok:
        res["problems"].append(f"{label}: differences outside V3_RULES 12.3 (variables {sorted(set(vars_) - set(allowed_vars))}, meta {sorted(set(r['meta_keys']) - set(allowed_meta))}, "
                               f"index {list(r['index_changes'])}, only_old {r['only_in_old']}, only_new {r['only_in_new']}, attributes {r['attributes']}) or a value check failed: {notes}")
    return ok


sha = {}
# ---- F1 / F2 against the registered networks: ship links only, S-A values
for rid in ("F1", "F2"):
    f, want = REG[rid]; r = compare(REG_DIR / f, FILES[rid]); sha[rid] = r["sha256_new"]
    assert r["sha256_old"] == want, f"{f} is not the registered file"
    n = pypsa.Network(str(FILES[rid])); L = n.links; ships = L.index[L.carrier.isin(SHIP)]
    mc, ef = r["variables"].get("links_marginal_cost", {}), r["variables"].get("links_efficiency", {})
    key = {"oil non-fossil ship": "oil", "methanol ship": "methanol", "ammonia ship": "ammonia"}
    want_mc = pd.Series([rv(f"liquid_ship_fixed_ieaghg_{key[c]}") + rv(f"liquid_ship_ckm_ieaghg_{key[c]}") * km for c, km in zip(L.loc[ships, "carrier"], L.loc[ships, "route_km"].astype(float))], index=ships)
    notes = dict(ship_links=int(len(ships)), marginal_cost_differing_equals_ship_links=sorted(mc.get("differing", [])) == sorted(ships), efficiency_differing_equals_ship_links=sorted(ef.get("differing", [])) == sorted(ships),
                 sa_marginal_cost_max_rel_dev=float(((L.loc[ships, "marginal_cost"] - want_mc).abs() / want_mc).max()), efficiency_all_one=bool((L.loc[ships, "efficiency"] == 1.0).all()),
                 ship_cost_basis=(r["meta_keys"].get("research_config.liquids.ship_cost_basis")), path=r["meta_keys"].get("s2_layers.geothermal.bus_mapping_source.path"),
                 path_sha256_same=n.meta["s2_layers"]["geothermal"]["bus_mapping_source"]["sha256"] == pypsa.Network(str(REG_DIR / f)).meta["s2_layers"]["geothermal"]["bus_mapping_source"]["sha256"])
    allowed_meta = set(META_SHIP)
    if rid == "F2":
        allowed_meta.add("research_variant.base.sha256"); notes["variant_base_sha256_is_new_F1"] = n.meta["research_variant"]["base"]["sha256"] == sha["F1"]
    # 270 ship links = 90 directed routes x 3 carriers (V3_RULES 3.3); section 12.3 as written before the builds said "810" by a counting error, corrected after this check (the rule is the set of ship links)
    notes["ship_links_by_carrier"] = L.loc[ships, "carrier"].value_counts().to_dict()
    ok = (len(ships) == 270 and notes["ship_links_by_carrier"] == {c: 90 for c in SHIP} and notes["marginal_cost_differing_equals_ship_links"] and notes["efficiency_differing_equals_ship_links"] and notes["sa_marginal_cost_max_rel_dev"] <= 1e-12
          and notes["efficiency_all_one"] and notes["ship_cost_basis"] == ["td_tanker", "ieaghg"] and notes["path_sha256_same"] and notes.get("variant_base_sha256_is_new_F1", True))
    judge(f"{rid}_vs_registered", r, {"links_marginal_cost", "links_efficiency"}, allowed_meta, ok, notes)
# ---- F3 / F4 against F1 / F2: the fleet proxy only, bit-wise 0.5 x
for rid, base in (("F3", "F1"), ("F4", "F2")):
    r = compare(FILES[base], FILES[rid]); sha[rid] = r["sha256_new"]
    a, b = pypsa.Network(str(FILES[base])), pypsa.Network(str(FILES[rid]))
    ev = a.stores.index[a.stores.carrier == "EV battery"]; ch = a.links.index[a.links.carrier == "BEV charger"]
    se, lp = r["variables"].get("stores_e_nom", {}), r["variables"].get("links_p_nom", {})
    half = lambda x, y: bool(np.array_equal((x.to_numpy(dtype="f8") * 0.5).view("u8"), y.to_numpy(dtype="f8").view("u8")))
    notes = dict(ev_batteries=int(len(ev)), chargers=int(len(ch)), e_nom_differing_equals_ev=sorted(se.get("differing", [])) == sorted(ev), p_nom_differing_equals_chargers=sorted(lp.get("differing", [])) == sorted(ch),
                 e_nom_bitwise_half=half(a.stores.loc[ev, "e_nom"], b.stores.loc[ev, "e_nom"]), p_nom_bitwise_half=half(a.links.loc[ch, "p_nom"], b.links.loc[ch, "p_nom"]),
                 battery_twh=[float(a.stores.loc[ev, "e_nom"].sum() / 1e6), float(b.stores.loc[ev, "e_nom"].sum() / 1e6)], charger_gw=[float(a.links.loc[ch, "p_nom"].sum() / 1e3), float(b.links.loc[ch, "p_nom"].sum() / 1e3)],
                 fleet_scale=[a.meta["research_ev"]["fleet_scale"], b.meta["research_ev"]["fleet_scale"]], overrides=b.meta["research_config"].get("config_overrides"))
    allowed_meta = set(META_EV)
    if rid == "F4":
        allowed_meta.add("research_variant.base.sha256"); notes["variant_base_sha256_is_F3"] = b.meta["research_variant"]["base"]["sha256"] == sha["F3"]
    ok = (len(ev) == 96 and len(ch) == 96 and notes["e_nom_differing_equals_ev"] and notes["p_nom_differing_equals_chargers"] and notes["e_nom_bitwise_half"] and notes["p_nom_bitwise_half"]
          and notes["fleet_scale"] == [1.0, 0.5] and notes.get("variant_base_sha256_is_F3", True)
          # the override record = the parent's record + the fleet override (a variant also records its own set, F2: cross_border.stock_mode=no_new_xb)
          and sorted(notes["overrides"] or []) == sorted(list(a.meta["research_config"].get("config_overrides") or []) + ["s2.demand.ev_fleet_scale=0.5"]))
    notes["overrides_parent"] = a.meta["research_config"].get("config_overrides")
    judge(f"{rid}_vs_{base}", r, {"stores_e_nom", "links_p_nom"}, allowed_meta, ok, notes)
# ---- scenario difference: F2 - F1 and F4 - F3 with the structure of the registered pair (review dimension 4)
ref = compare(REG_DIR / REG["F1"][0], REG_DIR / REG["F2"][0])


def structure(r):
    return dict(index={k: (sorted(v["removed"]), sorted(v["added"])) for k, v in r["index_changes"].items()},
                variables={k: (v.get("n_differing"), sorted(v.get("differing", [])), json.dumps(v.get("values"), sort_keys=True, default=str)) for k, v in r["variables"].items()},
                only=(r["only_in_old"], r["only_in_new"]), attributes=r["attributes"], meta=sorted(r["meta_keys"]))


def carriers_removed(old_file, names, lst):
    n = pypsa.Network(str(old_file)); d = n.df(lst)
    return d.loc[[x for x in names if x in d.index], "carrier"].astype(str).value_counts().to_dict()


for lab, i, d in (("F2_minus_F1", "F1", "F2"), ("F4_minus_F3", "F3", "F4")):
    r = compare(FILES[i], FILES[d]); s, t = structure(r), structure(ref)
    same = {k: s[k] == t[k] for k in s}
    rm_lines = r["index_changes"].get("lines_i", {}).get("removed", []); rm_links = r["index_changes"].get("links_i", {}).get("removed", [])
    common = {k: v.get("n_differing") for k, v in r["variables"].items() if v.get("n_differing")}
    notes = dict(same_structure_as_registered_pair=same, removed_lines=len(rm_lines), removed_links=len(rm_links), removed_links_by_carrier=carriers_removed(FILES[i], rm_links, "Link"),
                 removed_lines_by_carrier=carriers_removed(FILES[i], rm_lines, "Line"), changed_on_common_components=common,
                 time_series_differing_on_common_columns={k: v.get("n_differing") for k, v in r["variables"].items() if "_t_" in k and v.get("n_differing")})
    ok = all(same.values()) and len(rm_lines) == 46 and len(rm_links) == 283 and notes["removed_links_by_carrier"] == {"H2 pipeline": 110, "gas pipeline": 110, "CO2 pipeline": 55, "DC": 8} \
        and set(common) == {"lines_s_nom_extendable", "lines_s_nom_max", "links_p_nom_extendable", "links_p_nom_max"} and common.get("lines_s_nom_max") == 16 and common.get("links_p_nom_max") == 9 \
        and not notes["time_series_differing_on_common_columns"]
    res["comparisons"][lab] = dict(passed=bool(ok), notes=notes, meta_keys=sorted(r["meta_keys"]))
    if not ok:
        res["problems"].append(f"{lab}: scenario difference differs from the registered pair / review dimension 4: {notes}")
res["sha256"] = sha; res["bytes"] = {k: v.stat().st_size for k, v in FILES.items()}
res["passed"] = not res["problems"]
(EV / "F_REBUILD_CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps(dict(passed=res["passed"], problems=res["problems"], sha={k: v[:8] for k, v in sha.items()}, comparisons={k: v["passed"] for k, v in res["comparisons"].items()}), default=str))
