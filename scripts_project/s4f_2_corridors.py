"""S4F-2 data (decision 97 a, b, d): TH-MY stock correction table, APG #4 Indonesian endpoint, SG-VN / SG-KH optional candidates.

  a. TH_MY_STOCK_S4F2.csv: the four OSM 250878579 HVDC records are duplicates of Khlong Ngae - Gurun (same OSM way split -1..-4, identical geometry
     100.45E 6.71N - 100.54E 5.81N, 300 kV, single circuit, dc=True; data/osm-plus-prebuilt/0.1.1/all_lines_build_network.csv) -> removed; Khlong
     Ngae - Gurun keeps 300 MW (AIMS new_links.csv: existing, 2002, 300 MW); line 91 -> 80 MW (s_nom, s_nom_min; grade C: cluster artefact, its member
     lines are not Sadao - Chuping - S4F_STOP_01_LINE91.md; 80 MW = AIMS line type 94-AL1/15-ST1A 0.35 kA x 132 kV x sqrt3 of Sadao - Chuping in
     AIMS new_lines.csv = APG 380 - 300). TH-MY 2025 total 380 MW. Applied at build time (s4f_layers.apply_th_my_stock); the frozen base is unchanged.
  b. CORRIDORS_S4F2.csv = CORRIDORS_S4E1.csv with the APG #4 row moved to ID_Sumatra3 3 (Pekanbaru) - MY_Peninsular2 1: length great-circle x 1.25,
     subsea share by the S4C supplement 01 rule (s4c_1_subsea_shares.classify + same-landmass rule), as in S4E-1; #16 keeps the Batam end.
  d. OPTIONAL_CORRIDORS_S4F2.csv: SG-VN and SG-KH (APG 'other initiative') at the nearest node pairs of S4E-1 (APG_CROSS_SEA_S4E1.csv), same
     parameters; appended only with research.corridors.optional_sg_vn_kh = on (second-batch sensitivity).
  SUBSEA_SHARE_S4F2.csv = SUBSEA_SHARE_S4E1.csv + the new node pairs (same method); --fill-from adds the pairs created by topology side effects
  (second pass, as in S4E-1).

    python scripts_project/s4f_2_corridors.py --network <S4E integrated build>
    python scripts_project/s4f_2_corridors.py --fill-from <build with --override corridors.subsea_share=zero>
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from pyproj import Geod

from d1_common import REG_DIR, ROOT, Registry, sha256
from s4c_1_subsea_shares import AUTHOR, classify

SCRIPT = "scripts_project/s4f_2_corridors.py"
INSTRUCTION_SHA = "28d7458d47e282df6aaf5fa324e3772b886a67f9b178dd728696c5eac7216f03"
LOC = "work/p1_step4f_20261017/S4F_CLAUDE_CODE_INSTRUCTION.md"
SRC = "S4F instruction S4F-2 (user decisions 2026-10-17 14:43 SGT; TH-MY rule of the reply to S4F_STOP_01)"
C = ROOT / "research_inputs/corridors"
AIMS = ROOT / "data/transmission_projects/AIMS"
OSM = ROOT / "data/osm-plus-prebuilt/0.1.1/all_lines_build_network.csv"
LENGTH_FACTOR = 1.25
APG4_NEW = ("ID_Sumatra3 3", "MY_Peninsular2 1")
OPTIONAL = [("other1", "SG2 0", "VN2 0", "Singapore - Vietnam"), ("other2", "KH2 0", "SG2 0", "Singapore - Cambodia")]
DUPLICATES = [f"250878579-{i}_0" for i in range(1, 5)]


def geometry_tools():
    land = gpd.read_file(AUTHOR / "country_shapes.geojson").union_all(); off = gpd.read_file(AUTHOR / "offshore_shapes.geojson").union_all()
    shapely.prepare(land); shapely.prepare(off); polys = list(land.geoms); tree = shapely.STRtree(polys)
    return land, off, polys, tree, Geod(ellps="WGS84")


def landmass(b, node, polys, tree):
    pt = shapely.Point(float(b.at[node, "x"]), float(b.at[node, "y"])); hit = tree.query(pt, predicate="intersects")
    if len(hit):
        return int(hit[0]), 0.0
    j = int(tree.nearest(pt)); return j, float(polys[j].distance(pt))


def corridor_row(b, p, q, tools, name, status, sub_cols):
    land, off, polys, tree, geod = tools
    v = classify(geod, land, off, float(b.at[p, "x"]), float(b.at[p, "y"]), float(b.at[q, "x"]), float(b.at[q, "y"]))
    (l0, o0), (l1, o1) = landmass(b, p, polys, tree), landmass(b, q, polys, tree); same = l0 == l1
    share = 0.0 if same else v["subsea_share_not_land"]; typ, car = ("Line", "AC") if same else ("Link", "DC")
    if typ == "Link":
        name = name if name.endswith(" DC") else name + " DC"
    cp, cq = str(b.at[p, "country"]), str(b.at[q, "country"])
    row = {"from": p, "to": q, "carrier": car, "length_km": v["great_circle_km"] * LENGTH_FACTOR, "subsea_share": share,
           "source": "S4F-2 (scripts_project/s4f_2_corridors.py): great-circle x 1.25; subsea share S4C supplement 01 rule", "component_type": typ, "component": name,
           "country_from": cp, "country_to": cq, "capacity_2025_mw": 0.0, "nominal_mw_in_base": 0.0, "nominal_minus_lower_bound_mw": 0.0, "status": status}
    key = tuple(sorted((p, q)))
    geo = dict(loc0=key[0], loc1=key[1], country0=str(b.at[key[0], "country"]), country1=str(b.at[key[1], "country"]), cross_border=cp != cq, candidate=True, **v,
               components=f"{typ}:{car}", n_components=1, names=name, check_expectation="", check_label=status.split(" (")[0],
               landmass0=(l0 if key[0] == p else l1), landmass1=(l1 if key[0] == p else l0), offland_deg0=(o0 if key[0] == p else o1), offland_deg1=(o1 if key[0] == p else o0),
               same_landmass=same, share_zero=0.0, share_geometric_all=v["subsea_share_not_land"], share_landmass_nonland=share,
               main_rule=("same landmass -> 0 (overland route)" if same else "different landmass -> not-land share"))
    return row, {k: geo.get(k) for k in sub_cols}


def th_my_table() -> pd.DataFrame:
    nl = pd.read_csv(AIMS / "new_lines.csv", index_col=0); nk = pd.read_csv(AIMS / "new_links.csv", index_col=0)
    sc = nl.loc["Sadao – Chuping"]; kg = nk.loc["Khlong Ngae – Gurun"]
    i_nom = 0.35   # PyPSA standard line type 94-AL1/15-ST1A (i_nom 0.35 kA), the type of Sadao - Chuping in AIMS new_lines.csv
    if str(sc.type) != "94-AL1/15-ST1A 0.4" or int(sc.v_nom) != 132 or int(sc.num_parallel) != 1 or str(sc.project_status) != "existing":
        raise ValueError("AIMS Sadao - Chuping record changed")
    if int(kg.p_nom) != 300 or str(kg.project_status) != "existing" or int(kg.build_year) != 2002:
        raise ValueError("AIMS Khlong Ngae - Gurun record changed")
    ac = math.sqrt(3) * 132.0 * i_nom * 1
    osm = pd.read_csv(OSM, usecols=["line_id", "circuits", "voltage", "dc", "length", "geometry"])
    d = osm[osm.line_id.isin(DUPLICATES)]
    if len(d) != 4 or d.dc.nunique() != 1 or not bool(d.dc.iloc[0]) or d.voltage.nunique() != 1 or d.circuits.nunique() != 1:
        raise ValueError("OSM 250878579 records not as expected")
    rows = [dict(component_type="Link", component=k, action="remove", frozen_base_mw=491.4, corrected_mw=0.0, grade="B",
                 basis="duplicate of Khlong Ngae - Gurun: OSM way 250878579 split -1..-4 (osm-plus-prebuilt 0.1.1: "
                       f"dc=True, {int(d.voltage.iloc[0]/1000)} kV, {int(d.circuits.iloc[0])} circuit, {d.length.iloc[0]/1000:.1f} km, same geometry 100.45E 6.71N - 100.54E 5.81N)")
            for k in DUPLICATES]
    if abs(ac - 80.0) > 0.05:
        raise ValueError(f"Sadao - Chuping rating {ac:.3f} MW is not ~80 MW")
    rows.append(dict(component_type="Line", component="91", action="set_capacity", frozen_base_mw=380.0, corrected_mw=80.0, grade="C",
                     basis=f"cluster artefact: member lines are not Sadao - Chuping (S4F_STOP_01_LINE91.md); 80 MW = APG 380 - 300, consistent with the AIMS line "
                           f"type 94-AL1/15-ST1A (0.35 kA) x 132 kV x sqrt3 = {ac:.2f} MW of Sadao - Chuping (AIMS new_lines.csv: existing 1980, 1 circuit); "
                           "380 MW came from the author's readjust_existing_interconnections (AIMS 2024 total on the AC line); num_parallel and impedance unchanged"))
    rows.append(dict(component_type="Link", component="Khlong Ngae – Gurun", action="keep", frozen_base_mw=300.0, corrected_mw=300.0, grade="B",
                     basis="AIMS new_links.csv: Khlong Ngae - Gurun existing, 2002, 110 km, 300 MW (HVDC)"))
    return pd.DataFrame(rows)


def fill_missing_pairs(network: Path) -> list:
    """Second pass (as s4e_1_corridors.fill_missing_pairs) on SUBSEA_SHARE_S4F2.csv."""
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(network)); b = n.buses
    S = pd.read_csv(C / "SUBSEA_SHARE_S4F2.csv"); have = set(zip(S.loc0, S.loc1)); tools = geometry_tools(); land, off, polys, tree, geod = tools
    suffixes = (" gas", " H2", " co2 stored", " oil")

    def loc(bus):
        l = str(b.at[bus, "location"]) if "location" in b and str(b.at[bus, "location"]) not in ("", "nan") else bus
        if l not in b.index or (float(b.at[l, "x"]) == 0.0 and float(b.at[l, "y"]) == 0.0):
            for s in suffixes:
                if bus.endswith(s) and bus[: -len(s)] in b.index:
                    l = bus[: -len(s)]; break
        return l
    comps = [("Line", k, z.bus0, z.bus1, "AC") for k, z in n.lines.iterrows()]
    comps += [("Link", k, z.bus0, z.bus1, z.carrier) for k, z in n.links[n.links.carrier.isin(["DC", "B2B", "H2 pipeline", "CO2 pipeline", "gas pipeline"])].iterrows()]
    new = {}
    for typ, k, b0, b1, car in comps:
        key = tuple(sorted((loc(b0), loc(b1))))
        if key[0] == key[1] or key in have:
            continue
        new.setdefault(key, []).append(f"{typ}:{car}:{k}")
    rows = []
    for (l0, l1), names in sorted(new.items()):
        v = classify(geod, land, off, float(b.at[l0, "x"]), float(b.at[l0, "y"]), float(b.at[l1, "x"]), float(b.at[l1, "y"]))
        (m0, o0), (m1, o1) = landmass(b, l0, polys, tree), landmass(b, l1, polys, tree); same = m0 == m1
        c0, c1 = str(b.at[l0, "country"]), str(b.at[l1, "country"])
        rows.append(dict(loc0=l0, loc1=l1, country0=c0, country1=c1, cross_border=c0 != c1, candidate=True, **v, components=";".join(sorted({x.rsplit(":", 1)[0] for x in names})),
                         n_components=len(names), names=";".join(sorted(x.split(":", 2)[2] for x in names))[:400], check_expectation="", check_label="S4F-2 topology side effect (second pass)",
                         landmass0=m0, landmass1=m1, offland_deg0=o0, offland_deg1=o1, same_landmass=same, share_zero=0.0, share_geometric_all=v["subsea_share_not_land"],
                         share_landmass_nonland=(0.0 if same else v["subsea_share_not_land"]), main_rule=("same landmass -> 0 (overland route)" if same else "different landmass -> not-land share")))
    if rows:
        S = pd.concat([S, pd.DataFrame(rows)[S.columns]], ignore_index=True); S.to_csv(C / "SUBSEA_SHARE_S4F2.csv", index=False)
    return rows


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, default=None); ap.add_argument("--fill-from", type=Path, default=None)
    ap.add_argument("--registry", action="store_true", help="only rewrite the registry fragment s4f_2 from the current files"); a = ap.parse_args()
    if a.registry:
        write_registry(); print("registry fragment s4f_2 written"); return
    if a.fill_from is not None:
        rows = fill_missing_pairs(a.fill_from)
        js = json.loads((C / "CORRIDORS_S4F2.json").read_text())
        js["second_pass"] = dict(network=str(a.fill_from), added_pairs=[{k: r[k] for k in ("loc0", "loc1", "country0", "country1", "components", "great_circle_km", "same_landmass",
                                                                                              "share_landmass_nonland")} for r in rows])
        js.setdefault("second_passes", []).append(js["second_pass"])
        (C / "CORRIDORS_S4F2.json").write_text(json.dumps(js, indent=1, default=str)); print(json.dumps(js["second_pass"], indent=1, default=str))
        write_registry()
        return
    n = pypsa.Network(str(a.network)); b = n.buses; tools = geometry_tools()
    cor = pd.read_csv(C / "CORRIDORS_S4E1.csv", float_precision="round_trip"); sub = pd.read_csv(C / "SUBSEA_SHARE_S4E1.csv")
    sea = pd.read_csv(C / "APG_CROSS_SEA_S4E1.csv", dtype={"apg_no": str})
    old4 = cor[cor.component.astype(str).str.startswith("APG4 ")]
    if len(old4) != 1:
        raise ValueError("APG #4 row not unique")
    p, q = sorted(APG4_NEW)
    r4, g4 = corridor_row(b, p, q, tools, f"APG4 {p} - {q} DC", "S4F2_APG_CROSS_SEA_CANDIDATE (decision 97 b, from 94): APG AIMS III #4, Indonesian end ID_Sumatra3 3 "
                          "(Pekanbaru); capacity 0, extendable", sub.columns)
    C2 = cor.copy(); i4 = old4.index[0]
    C2 = pd.concat([C2.drop(index=i4), pd.DataFrame([r4])], ignore_index=True)
    opt_rows, opt_geo = [], []
    for no, s, t, label in OPTIONAL:
        p2, q2 = sorted((s, t))
        rr, gg = corridor_row(b, p2, q2, tools, f"APG{no} {p2} - {q2}", f"S4F2_OPTIONAL_CANDIDATE (decision 97 d): {label} (APG other initiative), second-batch "
                              "sensitivity research.corridors.optional_sg_vn_kh = on; capacity 0, extendable", sub.columns)
        opt_rows.append(rr); opt_geo.append(gg)
    have = set(zip(sub.loc0, sub.loc1)); S = sub.copy(); added_pairs = []
    for gg in [g4] + opt_geo:
        if (gg["loc0"], gg["loc1"]) not in have:
            S = pd.concat([S, pd.DataFrame([gg])[sub.columns]], ignore_index=True); added_pairs.append((gg["loc0"], gg["loc1"]))
    sea2 = sea.copy(); k = sea2.index[sea2.apg_no == "4"][0]
    sea2.loc[k, ["node_a", "node_b", "great_circle_km", "action"]] = [p, q, round(float(g4["great_circle_km"]), 1),
                                                                      "new candidate (decision 97 b: Indonesian end ID_Sumatra3 3, Pekanbaru; S4E-1 nearest pair ID_Sumatra2 0 replaced)"]
    T = th_my_table()
    C2.to_csv(C / "CORRIDORS_S4F2.csv", index=False); pd.DataFrame(opt_rows).to_csv(C / "OPTIONAL_CORRIDORS_S4F2.csv", index=False)
    S.to_csv(C / "SUBSEA_SHARE_S4F2.csv", index=False); sea2.to_csv(C / "APG_CROSS_SEA_S4F2.csv", index=False); T.to_csv(C / "TH_MY_STOCK_S4F2.csv", index=False)
    summ = dict(apg4=dict(old=old4.iloc[0][["from", "to", "component", "length_km", "subsea_share"]].to_dict(), new={k: r4[k] for k in ("from", "to", "component", "length_km", "subsea_share", "component_type")},
                          great_circle_km=float(g4["great_circle_km"]), same_landmass=bool(g4["same_landmass"])),
                optional=[{k: r[k] for k in ("from", "to", "component", "component_type", "length_km", "subsea_share")} for r in opt_rows],
                subsea_pairs_added=[list(x) for x in added_pairs], th_my=T.to_dict("records"),
                th_my_total_before_mw=float(T.frozen_base_mw.sum()), th_my_total_after_mw=float(T.corrected_mw.sum()),
                sources=dict(corridors_s4e1=sha256(C / "CORRIDORS_S4E1.csv"), subsea_s4e1=sha256(C / "SUBSEA_SHARE_S4E1.csv"), aims_new_lines=sha256(AIMS / "new_lines.csv"),
                             aims_new_links=sha256(AIMS / "new_links.csv"), osm_prebuilt=sha256(OSM), network=str(a.network)))
    (C / "CORRIDORS_S4F2.json").write_text(json.dumps(summ, indent=1, default=str))
    write_registry()
    print(json.dumps({k: summ[k] for k in ("apg4", "optional", "subsea_pairs_added", "th_my_total_before_mw", "th_my_total_after_mw")}, indent=1, default=str))
    print(T.to_string())


def write_registry():
    """Registry fragment s4f_2 from the current S4F-2 files (re-run after the second pass, the length shares and the readjust audit)."""
    js = json.loads((C / "CORRIDORS_S4F2.json").read_text()); r4 = js["apg4"]["new"]; g4 = dict(great_circle_km=js["apg4"]["great_circle_km"])
    T = pd.read_csv(C / "TH_MY_STOCK_S4F2.csv", dtype={"component": str})
    reg = Registry(SCRIPT)
    reg.add("th_my_line91_s_nom_2025", "Decision 97 a: line 91 (TH-MY AC, frozen base 380 MW from the author's readjust_existing_interconnections = AIMS 2024 TH-MY total "
            "incl. HVDC) set to 80 MW = APG 380 - 300, consistent with the Sadao - Chuping rating (AIMS line type 94-AL1/15-ST1A 0.35 kA x 132 kV x sqrt3 = 80.02 MW). "
            "Cluster artefact: the "
            "member lines of line 91 are not Sadao - Chuping (S4F_STOP_01_LINE91.md); num_parallel and impedance unchanged", float(T.set_index("component").at["91", "corrected_mw"]),
            "MW", "C", "AIMS transmission projects new_lines.csv (Sadao - Chuping); PyPSA standard line type 94-AL1/15-ST1A", "data/transmission_projects/AIMS/new_lines.csv",
            sha256(AIMS / "new_lines.csv"), sensitivity_low=80.0, sensitivity_high=380.0, decision_ref="97")
    reg.add("th_my_hvdc_khlong_ngae_gurun_2025", "Decision 97 a: Khlong Ngae - Gurun HVDC 2025 stock 300 MW (AIMS: existing, 2002, 110 km); the four OSM 250878579 records "
            "(491.4 MW each) are duplicates of it and are removed; TH-MY total 380 MW = APG", 300.0, "MW", "B", "AIMS transmission projects new_links.csv",
            "data/transmission_projects/AIMS/new_links.csv", sha256(AIMS / "new_links.csv"), decision_ref="97")
    reg.add("s4f2_th_my_stock", "Decision 97 a: research.network.th_my_stock = apg_aims (main: TH_MY_STOCK_S4F2.csv applied at build time - 4 duplicate HVDC records removed, "
            "line 91 = 80 MW, Khlong Ngae - Gurun 300 MW; data correction of the frozen electric base, the base file and its SHA anchor unchanged) | frozen_base "
            "(original 2,645.6 MW, comparison)", "apg_aims|frozen_base", "flag", "B", SRC, "research_inputs/corridors/TH_MY_STOCK_S4F2.csv", sha256(C / "TH_MY_STOCK_S4F2.csv"),
            decision_ref="97,15", status="REFERENCE_ONLY")
    reg.add("s4f2_apg4_endpoint", f"Decision 97 b: APG #4 Peninsular Malaysia - Sumatera Indonesian end moved to ID_Sumatra3 3 (Pekanbaru): great-circle "
            f"{g4['great_circle_km']:.1f} km x 1.25 = {r4['length_km']:.1f} km, subsea share {r4['subsea_share']:.3f} ({r4['component_type']}); #16 keeps the Batam end",
            "ID_Sumatra3 3", "flag", "B", SRC, "research_inputs/corridors/CORRIDORS_S4F2.csv", sha256(C / "CORRIDORS_S4F2.csv"), decision_ref="97,94", status="REFERENCE_ONLY")
    reg.add("s4f2_sensitivity_sg_vn_kh", "Decision 97 d (second batch, registered, not run): SG-VN and SG-KH (APG other initiatives) as candidates, research.corridors."
            "optional_sg_vn_kh = on (OPTIONAL_CORRIDORS_S4F2.csv); main off", "off|on", "flag", "B", SRC, "research_inputs/corridors/OPTIONAL_CORRIDORS_S4F2.csv",
            sha256(C / "OPTIONAL_CORRIDORS_S4F2.csv"), decision_ref="97,94", status="REFERENCE_ONLY")
    reg.add("s4f2_lao_vn_store", "Decision 97 c: research.co2.lao_transit_vn_store = on (main: after the rail transit to a Vietnamese coastal node, Lao CO2 can enter the "
            "Vietnamese national store; land leg on the link, VN store unit cost on the store, inside the VN annual cap; carrier 'CO2 transit rail', trade class, both "
            "scenarios) | off", "on|off", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="97,95,93", status="REFERENCE_ONLY")
    for f, desc, script in [("CORRIDORS_S4F2.csv", "corridor table of the main run: CORRIDORS_S4E1.csv with the APG #4 row moved to ID_Sumatra3 3", SCRIPT),
                            ("SUBSEA_SHARE_S4F2.csv", "subsea share table: SUBSEA_SHARE_S4E1.csv rows unchanged + the S4F-2 node pairs and the second-pass pairs (same method)", SCRIPT),
                            ("XB_LENGTH_SHARES_S4F2.csv", "in-country length shares of every cross-border line / link of the S4F builds incl. the optional SG-VN / SG-KH "
                             "candidates (ledger sensitivity of decision 91a; method of s4d_3_data.length_shares)", "scripts_project/s4f_2_length_shares.py"),
                            ("AUTHOR_READJUST_LINES_S4F2.csv", "record only (no model change): cross-border AC lines whose s_nom the author's "
                             "readjust_existing_interconnections set to the AIMS 2024 totals (s_nom vs line-type rating, x, AC loop) - user decision item",
                             "scripts_project/s4f_2_readjust_audit.py")]:
        if (C / f).exists():
            reg.add("s4f2_" + f.split(".")[0].lower(), "Decision 97: " + desc, "table", "flag", "B", f"derived ({script})", "research_inputs/corridors/" + f,
                    sha256(C / f), decision_ref="97", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4f_2.csv")


if __name__ == "__main__":
    main()
