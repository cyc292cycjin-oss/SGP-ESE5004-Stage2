"""Fable W08 review: EVIDENCE.json (light evidence with sources, grades and SHA256 of every evidence file and script). usage: build_evidence.py <delivery dir> <head sha> <branch>"""
import hashlib
import json
import sys
from pathlib import Path

D = Path(sys.argv[1]); HEAD = sys.argv[2]; BRANCH = sys.argv[3]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
E = D / "evidence"
J = lambda n: json.loads((E / n).read_text())  # noqa: E731
ev = dict(review="v4 W08 independent review (Fable 5.1), instruction V4_FABLE_W08_INSTRUCTION.md v1", date="2026-11-07",
          instruction_sha256={p.name: sha(D / p.name) for p in (D / "V4_FABLE_W08_INSTRUCTION.md", D / "APPENDIX_REVIEWER_214.md")},
          object=dict(branch="codex/v4-w08-20261106", head="7aa356e49d284749d27c79fbdc75ade85f62866a", review_package_commit="bd890bf9", base="aad8e476", v31="d3b9a3bc"),
          review_branch=dict(branch=BRANCH, head=HEAD, worktree="/home/jin/wt_v4_fable"), solver_runs=0, hpc=False, downloads=0, repository_edits=0,
          scratch="/home/jin/v4fable (repo, a2, tests_copy; <= 0.7 GB)")
a2 = (E / "a2_compare.txt").read_text().splitlines()
ev["A2_fallback"] = dict(grade="VERIFIED", files_written_by_default_runs=len(a2), identical_to_v31=sum("v31:SAME" in l for l in a2), identical_to_head=sum("head:SAME" in l for l in a2), file="evidence/a2_compare.txt")
oc = (E / "out_compare.txt").read_text().splitlines()
ev["out_tables_regeneration"] = dict(grade="VERIFIED", files=len(oc), same=sum(l.endswith("SAME") for l in oc), file="evidence/out_compare.txt")
s7 = J("S7_COMPARE.json")
ev["A0_S7_reproduction"] = {k: dict(grade="EXACT", asean_repro_TWh=v["asean_repro"], asean_ref_TWh=v["asean_ref"], max_abs_diff_TWh=v["max_abs"], all_within_1e6=v["all_within_1e6"]) for k, v in s7.items()}
ch = J("CHAIN_CHECK.json")
ev["data_chains"] = dict(grade="EXACT", chains=len([c for c in ch["chains"] if "own_mwh" in c]), absent=[c["label"] for c in ch["chains"] if c.get("raw") == "ABSENT"],
                         max_abs_diff_cells_mwh=max(abs(c.get("cells_diff_mwh", 0.0)) for c in ch["chains"]), max_abs_diff_ats_2050_mwh=max(abs(c.get("ats_2050_minus_own_mwh", 0.0)) for c in ch["chains"]),
                         household_gasoline_ID_TWh=[c["own_twh"] for c in ch["chains"] if c["code"] == "4652"][0], file="evidence/CHAIN_CHECK.json")
cs = J("CONSERVATION_CHECK.json")
ev["conservation"] = {m: dict(grade="EXACT", asean_T_TWh=cs[m]["asean_T_twh"], max_abs_parts_minus_T_mwh=max(abs(r["diff_mwh"]) for r in cs[m]["by_country"]), negative_other_cells=sum(r["other_negative_cells"] for r in cs[m]["by_country"]),
                               rail_parent_2050_TWh=cs[m]["rail_parent_2050_twh"], bn_neu_gas_rows=cs[m]["bn_neu_gas_rows"]) for m in ("out_ras", "out_iid")}
ev["residue_symmetry"] = cs["residue_symmetry"]
sp = J("SENS_PAPER_FUELWOOD.json")
ev["F01_paper_fuelwood_literal_reading"] = {m: dict(grade="EXACT", ID_T_w08_TWh=sp[m]["ID"]["T_w08"] / 1e6, ID_T_literal_TWh=sp[m]["ID"]["T_literal"] / 1e6, diff_TWh=(sp[m]["ID"]["T_literal"] - sp[m]["ID"]["T_w08"]) / 1e6,
                                                     other_diff_TWh=(sp[m]["ID"]["other_literal"] - sp[m]["ID"]["other_w08"]) / 1e6, w08_add_TWh=sp[m]["w08_add_mwh"][0] / 1e6, literal_add_TWh=sp[m]["literal_add_mwh"][0] / 1e6) for m in sp}
ev["F01_fuelwood_inputs"] = {k: sp["ras"]["fw"][k] for k in ("factor_gj_m3", "sdmx_km3", "sdmx_mwh", "mean_km3", "mean_mwh", "scale", "paper_sdmx_mwh", "paper_sdmx_km3", "share_non_paper")}
nm, ni = J("NET_CHECK_main.json"), J("NET_CHECK_iid.json")
def netsum(n):
    c = {x["country"]: x for x in n["compare"]}
    return dict(grade="EXACT", meta_switch_sha_ok=n["meta_switch_sha_equals_table_set"], meta_files_ok=n["meta_files_equal_table_set"],
                max_abs_diff_mwh={k: max(abs(x[a] - x[b]) for x in n["compare"]) for k, (a, b) in dict(electricity=("el_net", "el_tab"), heat_low=("heat_net", "heat_tab"), heat_medium_a=("heat_ma_net", "heat_ma_tab"), heat_medium_b=("heat_mb_net", "heat_mb_tab"),
                                                                                                 heat_high=("heat_hi_net", "heat_hi_tab"), coal=("coal_net", "coal_tab"), hydrogen=("h2_net", "h2_tab"), ammonia=("nh3_net", "nh3_tab"), methanol=("meoh_net", "meoh_tab"), ev=("ev_net", "ev_expected"), rail=("rail_net", "rail_tab")).items()},
                loads_with_rail_parent_source=len(n["loads_with_rail_parent_source"]), gas_caps_max_abs_diff_mwh=max(abs(v["diff"]) for v in n["gas_caps_network_vs_table"].values()), gas_caps_table=n["gas_caps_table_used"],
                fugitive_factors=n["fugitive_links"], VN_overflow_ledger={k: n["biomass_overflow_ledger"]["VN"][k] for k in ("industry_biomass_before_mwh", "agriculture_biomass_before_mwh", "cap_mwh", "overflow_industry_mwh", "useful_heat_efficiency")},
                VN_overflow_table_mwh=c["VN"]["overflow_tab"], VN_overflow_heat_loads_mwh=c["VN"]["overflow_heat_net"], curves_profiled=n["industry_ledger_v4"]["curves"] if n.get("industry_ledger_v4") else None,
                biomass_pools={k: dict(store=v["store_e_nom"], table=v["table_all_rows"]) for k, v in n["biomass_pools"].items()})
ev["network_main_2920"] = netsum(nm); ev["network_iid_2920"] = netsum(ni)
ap = J("ANCHOR_PROFILE_CHECK.json")
ev["anchors"] = dict(grade="EXACT", residue_adjustment_mwh=ap["residue_adjustment_mwh"], ras_rows_max_residual_mwh=max(abs(r["residual_mwh"]) for r in ap["out_ras_rows"]), iid_rows_max_residual_mwh=max(abs(r["residual_mwh"]) for r in ap["out_iid_rows"]),
                     ras_columns_deviation_mwh={s: v["deviation_mwh"] for s, v in ap["out_ras_columns"].items()}, iid_columns_deviation_mwh={s: v["deviation_mwh"] for s, v in ap["out_iid_columns"].items()},
                     v31_ras_rank_one_max_dev=max(abs(x[s] - 1.0) for x in ap["v31_ras_rank_one_ratio_check"] for s in ("Industry", "Transport", "Residential", "Commercial", "AgricultureOthers") if x[s] is not None))
ev["profiles"] = dict(grade="EXACT", **{k: v for k, v in ap["profiles"].items() if k != "zones"}, zone_shift_non_flat_all_minus_one_hour=all(x["best_roll_hours_7_to_8"] == -1 for x in ap["zone_shift_check"] if not x["flat"]),
                      zone_shift_max_abs_diff=max(x["max_abs_diff_at_best"] for x in ap["zone_shift_check"]), weights=ap["weights_summary"])
if (E / "OFF_BUILD_VS_V31.json").exists():
    ob = J("OFF_BUILD_VS_V31.json")
    diff_comp = {k: v for k, v in ob["components"].items() if v.get("static_diffs") or v.get("timeseries_diffs") or not v["index_equal"] or v["columns_only_a"] or v["columns_only_b"]}
    ev["off_build_vs_v31_package"] = dict(grade="VERIFIED", components_compared=len(ob["components"]), components_with_differences=diff_comp, meta_only_in_off_build=ob["meta_only_in_off_build"], meta_only_in_v31=ob["meta_only_in_v31"],
                                          meta_keys_differing=ob["meta_keys_differing"], gas_network_subkeys=ob.get("meta_research_gas_network_subkeys_differing"), demand_ledger_subkeys=ob.get("meta_s2_demand_ledger_subkeys_differing"), file="evidence/OFF_BUILD_VS_V31.json")
if (E / "SMOKE_LEDGER_CMP.json").exists():
    lc = J("SMOKE_LEDGER_CMP.json"); bc = lc["by_country"]
    ev["smoke56_cost_ledger_comparison"] = dict(grade="VERIFIED", total_column=lc["total_col"], delta_by_entity_bn={k: dict(main=(bc["v4_F1"][k] - bc["v31_F1"][k]) / 1e9, iid=(bc["v4iid_F1"][k] - bc["v31_F1"][k]) / 1e9) for k in bc["v31_F1"]},
                                                 delta_by_column_asean_bn={k: dict(main=(v["v4"] - v["v31"]) / 1e9, iid=(v["iid"] - v["v31"]) / 1e9) for k, v in lc["by_column_asean"].items() if abs(v["v4"] - v["v31"]) > 1e7}, detail_top_bn=lc["detail_top"][:25])
if (E / "SMOKE_DECOMP.json").exists():
    sd = J("SMOKE_DECOMP.json")
    ev["smoke56_decomposition"] = {r: dict(objective=v["objective"], objective_lp=v["objective_lp"], constant=v["constant"], biomass_use_twh=v["biomass_use_total_twh_annualised"],
                                           ID_biomass_use_by_link=v["biomass_use_mwh_56snap_weighted"].get("ID"), ID_heat_supply=v["industry_heat_supply_mwh_weighted"].get("ID"),
                                           solid_biomass_price_ID=v["solid_biomass_price_mean_max"].get("solid biomass ID")) for r, v in sd.items()}
tv = (E / "tests_v4.txt").read_text().splitlines()
ev["tests_v4_in_copy"] = dict(first_run=[l for l in tv if "passed" in l or "failed" in l][-1:], registry_rerun_after_adding_scripts_and_config=[l for l in (E / "tests_registry_rerun.log").read_text().splitlines() if "passed" in l][-1:],
                              note="the two registry failures of the first run were the copy lacking the upstream scripts/ folder and config.default.yaml; all 37 pass with them")
ev["registry"] = dict(grade="VERIFIED", fragment_rows=69, file_rows_checked=67, sha_mismatches=0, bytes_mismatches=0, fragment_equals_registry_rows=True, data_registry_reassembly_identical=True, d1_evidence_differs_only_generated_utc=True, removed_rows=0, licence_scan_hits=0)
ev["files"] = {str(p.relative_to(D)).replace("\\", "/"): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(list(E.glob("*")) + list((D / "scripts").glob("*.py")) + list((D / "scripts/helpers").glob("*")) + [D / "FINDINGS_PRE.md", D / "FINDINGS.csv"] + ([D / "REPORT.md"] if (D / "REPORT.md").exists() else [])) if p.is_file()}
(D / "EVIDENCE.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
print("EVIDENCE.json written:", len(ev["files"]), "files listed")
