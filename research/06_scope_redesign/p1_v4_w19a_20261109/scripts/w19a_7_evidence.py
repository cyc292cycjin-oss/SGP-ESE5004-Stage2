"""W19a: assemble the light EVIDENCE.json from the evidence files of this delivery (no new computation)."""
import json
from pathlib import Path

import pandas as pd

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109")
E = D / "evidence"


def j(name):
    return json.loads((E / name).read_text(encoding="utf-8"))


def main():
    kh = j("KH_CAP_BRACKET.json")
    nc = j("KH_NC_CROSSCHECK.json")
    reg = j("REGISTRY_TIERS_META.json")
    wacc = j("WACC_BASIS.json")
    top = pd.read_csv(D / "TOP30_STATUS.csv")
    ev = dict(
        step="V4 W19a (ledger W19; decisions 224, 225)",
        instruction=dict(file="V4_W19A_INSTRUCTION.md", sha256="e284f70ddd0d36e9c6cc3aaef45dc076bbfc9d4397abd29a7f21e251b5c5b9a5", matches_sha256_txt=True, tag="VERIFIED"),
        session=dict(model="claude-opus-5-5", effort="xhigh", other_sessions_running=0, gurobi_processes=0, mem_available_gib=9, tag="VERIFIED"),
        branch=dict(name="asean/v4-w19a-20261109", start="ac75354cf416cb811d7b446beb03ed6fbc030a83", worktree="/home/jin/wt_v4_w19a",
                    w14_package_commit="26c2e47d025fdd4e46cb278718d93aeddabbe984", commit_is_ancestor=True, remote_codex_heads=0, remote_asean_heads=74, tag="VERIFIED"),
        solver_calls=0, hpc=False, data_downloads=0,
        registry=dict(commit_sha256="a9798b0c91b215920e57c388a0c90192a8119a85c9c379389b651c3b1c594c4c", base_aad8e476_sha256="93dbeb439e5a11b46d49d44380352c9ac053f93e0a959bbd9af3de16ed0293d5",
                      rows=[reg["rows_old"], reg["rows_new"]], in_use=[reg["in_use_old"], reg["in_use_new"]], c_in_use=[reg["c_in_use_old"], reg["c_in_use_new"]],
                      added=reg["added"], removed=len(reg["removed"]), tier_changes=len(reg["tier_changes"]), status_changes=reg["status_changes"],
                      classes_462=reg["classes"], c_in_use_v4_main_reading=reg["effective_c_in_use_v4_main"], tag="EXACT"),
        v31_solutions=dict(F1=dict(nc_sha256="7508ec72ddce9a9d48be1dd9487a46f01dc067384e9794f755e41e710f2cdb7c", duals_sha256="bd60aa57f1b42aab0fbd2bcc72a7c256c3c077c1acff3fb4994811501f33e836"),
                           F2=dict(nc_sha256="4cc51892d748805f776493a35f54006a51086cab748d923dcedac0d76a9ee406", duals_sha256="b0eec1e98de82e5e4a291958ca2040c949e73bfc94cde5145fd79d8c6933bfc3"),
                           cache_dirs=["work/p1_v4_d2a_20261107/cache/7508ec72ddce9a9d_v1", "work/p1_v4_d2a_20261107/cache/4cc51892d748805f_v1"], direct_read_crosscheck="evidence/KH_NC_CROSSCHECK.json", tag="VERIFIED"),
        kh=dict(capture_net_t=dict(F1=14351452, F2=14453258), injection_t=1.8e6, exports_t=kh["exports"], cap_dual_eur_t=kh["cap_dual"],
                global_row_dual=dict(F1=nc["F1"]["duals"]["KH"]["global_row"], F2=nc["F2"]["duals"]["KH"]["global_row"]),
                marginal_route_eur_t=dict(F1="3.5129 + 6.8894 = 10.4023 (pipelines KH2 0->KH2 2->TH2 3)", F2="12.8104 (ship KH2 0->TH)"),
                bracket_own_exports=dict(db_t=kh["db"], dZ_F1=[kh["lower"]["F1"], kh["upper"]["F1"]], dZ_F2=[kh["lower"]["F2"], kh["upper"]["F2"]], dB6=kh["dB6_interval_own_exports"], tag="EXACT"),
                cap_non_binding=dict(dZ_F1=kh["cap_non_binding"]["F1"], dZ_F2=kh["cap_non_binding"]["F2"], dB6=kh["cap_non_binding"]["dB6"], binding_end_t=[29.98e6, 48.90e6], tag="INFERENCE"),
                first_order_d2a_d2b=kh["first_order"], proposed_range_t_per_a=dict(data=[1.8e6, 2.64e6], method=[0.9e6, 3.6e6], prospective_scenario=50e6, tag="PROPOSED"),
                ph=kh["ph"]),
        wacc=dict(uniform=dict(value=0.07, basis="not stated at source; used as real (S4R F7; registry 'real basis, INFERENCE'); no tax in the LP -> acts as a real pre-tax hurdle (INFERENCE)"),
                  country_table="real, post-tax, local currency (IEA nominal post-tax midpoints / MY + Damodaran CRP; IMF WEO Oct 2026 CPI 2028-2030; Fisher)",
                  iea_basis_quote="local currencies, nominal terms and after tax", iea_url="https://www.iea.org/reports/cost-of-capital-observatory/dashboard",
                  unification="r_real_pre = (1 + n / (1 - tau)) / (1 + pi) - 1 (tau INFERENCE, to verify)", summary=wacc["summary"], tag="EXACT given INFERENCE tax rates"),
        harvest_cap_025=dict(code="scripts_project/d1_biomass.py:50 HARVEST_MAIN = 0.25 (trunk: line 311; crop harvest residues: line 281)",
                             registry="biomass_constraint_harvest_residue_removal_max = 0.25 (A; registered low 0.5 > main: registry flaw, not changed)",
                             irena2022=dict(sha256="bf52f40b9ffafb65993c6593f1dca0010194f5f36fce7b753919ad11e3e60f17", where="p.42 fn 10, p.65 fn 17, p.85 fn 21",
                                            appendix_A="p.138: 4 %, 140 per ha, 2 t per OPT, 80 % water; no 0.25"),
                             irena2017=dict(sha256="53a30811bebd2eb7e62aed8d8d6e0b401a25a347cb807cfca1069d633f567b2f", where="PDF p.6 text + fn 1; PDF p.27 Table R-3"),
                             meaning="share of the harvest-residue mass that may be removed (the rest stays for soil quality / biodiversity); independent of the mass basis",
                             consistent_with_decision_224_3=True, tag="VERIFIED"),
        top30=dict(source="work/p1_v4_d2b_20261108/RERANK_D2B_TOP30.csv", status_counts=top.status_w19a.value_counts().to_dict(), reviewer_0500="not provided (not found in the workspace)"),
        literature="evidence/APPENDIX_LITERATURE.md; DOWNLOAD_CANDIDATES.csv",
    )
    (D / "EVIDENCE.json").write_text(json.dumps(ev, indent=1, default=str), encoding="utf-8")
    print("EVIDENCE.json", len(json.dumps(ev)))


if __name__ == "__main__":
    main()
