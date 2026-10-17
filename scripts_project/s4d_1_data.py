"""S4D-1 data (decision 93): CO2 export only from coastal nodes; Lao transit pricing; registry fragment s4d_1.

Coastal nodes: research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv (scripts_project/s4d_1_coastline.py; user decision 2026-10-17 on stop report
S4D_STOP_01: option A with the physical coastline - a node is coastal when its onshore region touches the coast, internal and archipelagic waters
included, or a sea port / LNG terminal is recorded at it, or it is a converter node within 5 km of the sea; river-only ports do not count).

Inland nodes reach the coast through the domestic CO2 pipeline candidates (decision 35, endogenous in both scenarios): checked here on the
S4C-6 integrated build (shortest domestic path to a coastal buffered node of the same country, km).

Lao transit (instruction S4D-1 item 3): per LA node one transit export link, unit cost = land unit cost x distance to the nearest usable port +
the extra-ASEAN unit cost (decision 89). Land unit cost: Stolaroff et al. (2021) Frontiers in Energy Research 9:639943, Table 2 'Unit costs
for truck and rail transport', cryogenic CO2: rail 0.044 $/t-km + 2 $/t (staging and loading at origin, text section 'Transport of CO2', from
Gao et al. 2011 and Roussanaly et al. 2017), truck 0.111 $/t-km; US dollars of 2018 (the paper converts Gao et al. 2011 to '2018 US dollars';
truck operating costs from ATRI 2017 data - INFERENCE that Table 2 is in 2018 $). Main: rail (Mt-scale flows; the paper recommends rail or
pipeline for large flows), grade C, +-50 % (instruction); truck kept as an alternative for the user decision. Distance: great-circle distance x
1.25, the routing factor of the model's CO2 / H2 pipeline candidates (PyPSA-Eur v2025.07.0 config.default.yaml lines 325, 341; equal to the median
length / great-circle ratio of the 19 existing cross-border AC lines, registry corridor_length_factor_frozen_base). Usable port (main): the nearest
point of the physical coast of an ASEAN neighbour (VN, TH, KH, MM; same sea mask as the coastal table), consistent with the user's reason that the
IEAGHG ship cost already contains port, buffer tanks and loading, so a coast suffices to build a CO2 loading terminal; the nearest existing sea port
of the author World Port Index subset (harbour type not River / Lake / Canal) is reported as the alternative. Liquefaction is not added: the
extra-ASEAN unit cost (IEAGHG 2004 chain) already contains it, and the CO2 travels liquid from the Lao loading station.

    python scripts_project/s4d_1_data.py --network <S4C-6 integrated_2920_3h_unsolved.nc> \
        --sources /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4d_20261017/sources_s4d/co2_land
"""
from __future__ import annotations

import argparse
import heapq
import json
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points, unary_union

import s4d_1_coastline as C
from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv
from s4c_4_data import deflator

SCRIPT = "scripts_project/s4d_1_data.py"
INSTRUCTION_SHA = "a35fa7d52c0d645830562e57fb242563b864994682eeb1ce6a2a8d59f73b2586"
OUT = ROOT / "research_inputs" / "co2_v5"
STOLAROFF = "Stolaroff_2021_FrontEnergyRes_9_639943.pdf"
STOLAROFF_URL = "https://www.frontiersin.org/articles/10.3389/fenrg.2021.639943/pdf"
RAIL_USD_PER_TKM, RAIL_LOADING_USD_PER_T, TRUCK_USD_PER_TKM = 0.044, 2.0, 0.111   # Table 2, cryogenic CO2
USD_YEAR = 2018
LENGTH_FACTOR = 1.25
PYPSA_EUR_CONFIG_SHA = "bfbe9160db09c3e960b97173bc755492b7638e0f4a5081ffaa1dddd4635da787"   # config.default.yaml v2025.07.0, as in the other registry rows citing it
SENS = 0.5
NEIGHBOURS = ("VN", "TH", "KH", "MM")   # ASEAN neighbours of LA with a coast (CN is outside the model)
USER_DECISION = ("user decision 2026-10-17 on S4D_STOP_01_COASTAL_NODES.md (chat): option A, corrected to the physical coastline consistent with the "
                 "'not-land' reading of supplement 01")


def hav_km(x0, y0, x1, y1):
    p0, p1 = np.radians(y0), np.radians(y1); dl = np.radians(x1 - x0)
    a = np.sin((p1 - p0) / 2) ** 2 + np.cos(p0) * np.cos(p1) * np.sin(dl / 2) ** 2
    return float(2 * 6371.0 * np.arcsin(np.sqrt(a)))


def pipeline_reach(network: Path, coastal: pd.DataFrame) -> pd.DataFrame:
    """Shortest domestic CO2-pipeline path (km, candidate lengths) from each inland buffered node to a coastal buffered node of the same country."""
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(network))
    pl = n.links[(n.links.carrier == "CO2 pipeline") & (n.links.border_class == "domestic")]
    loc = lambda b: b[: -len(" co2 stored")] if b.endswith(" co2 stored") else b
    g = {}
    for _, z in pl.iterrows():
        a, b, L = loc(z.bus0), loc(z.bus1), float(z.length)
        g.setdefault(a, []).append((b, L)); g.setdefault(b, []).append((a, L))
    buf = coastal[coastal.co2_buffer]
    coast_set = set(buf.node[buf.coastal])
    rows = []
    for _, r in buf[~buf.coastal].iterrows():
        dist = {r.node: 0.0}; prev = {}; pq = [(0.0, r.node)]; hit = None
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, np.inf):
                continue
            if u in coast_set:
                hit = u; break
            for v, L in g.get(u, []):
                if d + L < dist.get(v, np.inf):
                    dist[v] = d + L; prev[v] = u; heapq.heappush(pq, (d + L, v))
        path = []
        if hit:
            u = hit
            while u != r.node:
                path.append(u); u = prev[u]
            path = [r.node] + path[::-1]
        rows.append(dict(node=r.node, country=r.country, domestic_pipeline_ends=len(g.get(r.node, [])), reaches_coastal_node=bool(hit),
                         nearest_coastal_node=hit or "", path_km=round(dist[hit], 1) if hit else None, path="->".join(path)))
    return pd.DataFrame(rows)


def lao_transit(coastal: pd.DataFrame, rail_eur, load_eur, truck_eur) -> pd.DataFrame:
    land = gpd.read_file(C.LAND).to_crs(C.EQ); eez = gpd.read_file(C.EEZ).to_crs(C.EQ); on = gpd.read_file(C.REG_ON).to_crs(C.EQ).set_index("node")
    land_u = unary_union(land.geometry); eez_u = unary_union(eez.geometry)
    U = unary_union([land_u, eez_u])
    holes = [Polygon(r) for p in C.polys(U) for r in p.interiors]
    sea = unary_union([eez_u] + [h for h in holes if h.distance(eez_u) <= 1000.0]).buffer(-C.OPEN_M).buffer(C.OPEN_M)
    sea_touch = sea.buffer(C.TOUCH_M)
    coasts = {c: land.loc[land.name == c, "geometry"].iloc[0].boundary.intersection(sea_touch) for c in NEIGHBOURS}
    ports = pd.read_csv(OUT / "PORTS_ASEAN_TO_NODES_S4D1.csv")
    ports = ports[ports.country.isin(NEIGHBOURS)]
    sea_ports = ports[~ports.harbor_type.astype(str).str.contains("River|Lake|Canal", case=False)]
    to_ll = lambda g: gpd.GeoSeries([g], crs=C.EQ).to_crs("EPSG:4326").iloc[0]
    rows = []
    for _, r in coastal[coastal.country == "LA"].sort_values("node").iterrows():
        pt = gpd.GeoSeries([Point(r.x, r.y)], crs="EPSG:4326").to_crs(C.EQ).iloc[0]
        best = None
        for c, line in coasts.items():
            q = to_ll(nearest_points(pt, line)[1]); d = hav_km(r.x, r.y, q.x, q.y)
            if best is None or d < best[1]:
                best = (c, d, q)
        c, d, q = best
        qe = gpd.GeoSeries([q], crs="EPSG:4326").to_crs(C.EQ).iloc[0]
        owner = [i for i, g in on.geometry.items() if g.distance(qe) <= C.TOUCH_M + 1.0 and i in set(coastal.node[coastal.coastal])]
        pd_all = ports.assign(d=[hav_km(q.x, q.y, a, b) for a, b in zip(ports.x, ports.y)]).sort_values("d").iloc[0]
        sp = sea_ports.assign(d=[hav_km(r.x, r.y, a, b) for a, b in zip(sea_ports.x, sea_ports.y)]).sort_values("d").iloc[0]
        route = d * LENGTH_FACTOR; route_port = float(sp.d) * LENGTH_FACTOR
        rows.append(dict(node=r.node, x=r.x, y=r.y, coast_country=c, coast_point_x=round(q.x, 4), coast_point_y=round(q.y, 4), coastal_node_at_point="/".join(owner),
                         great_circle_km=round(d, 1), route_km=round(route, 1), nearest_port_record_to_coast_point=f"{pd_all.port} ({pd_all.country}, {pd_all.harbor_type}, {pd_all.d:.0f} km)",
                         land_cost_rail_eur2020_per_t=round(route * rail_eur + load_eur, 4), land_cost_truck_eur2020_per_t=round(route * truck_eur, 4),
                         alt_sea_port=f"{sp.port} ({sp.country}, {sp.harbor_type})", alt_port_great_circle_km=round(float(sp.d), 1), alt_port_route_km=round(route_port, 1),
                         alt_port_land_cost_rail_eur2020_per_t=round(route_port * rail_eur + load_eur, 4)))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--sources", type=Path, required=True); a = ap.parse_args()
    reg_tab = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    fred = ROOT / "research_inputs/registry_v5/sources/A191RD3A086NBEA.csv"
    us_y, us20 = deflator(fred, "observation_date", "A191RD3A086NBEA", USD_YEAR), deflator(fred, "observation_date", "A191RD3A086NBEA", 2020)
    fx = float(reg_tab.at["fx_usd_to_eur_2020", "value"]); f_usd = us20 / us_y * fx
    rail, load, truck = RAIL_USD_PER_TKM * f_usd, RAIL_LOADING_USD_PER_T * f_usd, TRUCK_USD_PER_TKM * f_usd
    extra = float(reg_tab.at["co2_extra_asean_storage_cost", "value"])
    pdf = a.sources / STOLAROFF; psha = sha256(pdf)
    coastal = pd.read_csv(OUT / "COASTAL_NODES_S4D1_FINAL.csv").merge(pd.read_csv(OUT / "COASTAL_NODES_S4D1.csv")[["node", "x", "y"]], on="node")
    csha = sha256(OUT / "COASTAL_NODES_S4D1_FINAL.csv")
    reach = pipeline_reach(a.network, coastal)
    write_csv(reach.to_dict("records"), OUT / "CO2_INLAND_PIPELINE_REACH_S4D1.csv", list(reach.columns))
    tr = lao_transit(coastal, rail, load, truck)
    tr["transit_unit_cost_eur2020_per_t"] = (tr.land_cost_rail_eur2020_per_t + extra).round(4)
    write_csv(tr.to_dict("records"), OUT / "LAO_TRANSIT_S4D1.csv", list(tr.columns))
    tsha = sha256(OUT / "LAO_TRANSIT_S4D1.csv"); rsha = sha256(OUT / "CO2_INLAND_PIPELINE_REACH_S4D1.csv")

    reg = Registry(SCRIPT); cfg = "configs/research/baseline.yaml"; ins = "work/p1_step4d_20261017/S4D_CLAUDE_CODE_INSTRUCTION.md"
    reg.add("s4d1_coastal_rule_user_decision", "Decision 93 coastal-node rule (" + USER_DECISION + "): a node is coastal when its onshore region touches the physical coast (any sea, internal "
            "and archipelagic waters included, e.g. the Bight of Bangkok and the Cambodian coast; not the EEZ alone), or a sea port / LNG terminal is recorded at it; river-only ports do "
            "not count; converter nodes within 5 km of the sea are coastal. Reason: the IEAGHG (2004) ship cost already contains port, buffer tanks and loading facilities, so a coast is "
            "enough to build a CO2 loading terminal; river ports are excluded for lack of draught. Re-judged: TH2 2 inland (only the Bangkok river port; its region stops 7.3 km from the "
            "Bight, the strip belongs to TH2 3), KH2 4 inland (region 44 km from the sea, the land between is TH2 3)", "physical_coast_or_sea_port", "flag", "B", USER_DECISION,
            ins, INSTRUCTION_SHA, decision_ref="93", status="REFERENCE_ONLY")
    js = json.loads((OUT / "COASTAL_NODES_S4D1_FINAL.json").read_text())
    reg.add("coastal_nodes_s4d1_final", f"Coastal-node table (decision 93): {js['coastal']} of {js['nodes']} nodes coastal; buffered nodes {js['buffered']['coastal']} coastal / "
            f"{js['buffered']['inland']} inland; basis per node (coast contact km, sea port, LNG, converter distance; inland: region distance to the sea and the region holding the land "
            "between) - research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv (scripts_project/s4d_1_coastline.py)", "table", "flag", "B",
            "author country_shapes / offshore_shapes; regions_onshore; author ports.csv (WPI); GEM LNG", "research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv", csha, decision_ref="93", status="REFERENCE_ONLY")
    reg.add("co2_extra_asean_export_nodes_switch", "research.co2.extra_asean_export_nodes values: coastal (main, decision 93: extra-ASEAN export links only at the coastal nodes of "
            "research.co2.coastal_nodes_table; inland CO2 reaches the coast through domestic CO2 pipelines, decision 35) | all (S4C-4 behaviour: every buffered node)", "coastal|all", "flag", "B",
            "S4D instruction S4D-1 item 2", cfg, INSTRUCTION_SHA, decision_ref="93", status="REFERENCE_ONLY")
    ok = reach[reach.country != "LA"]
    reg.add("co2_inland_pipeline_reach_s4d1", f"Inland buffered nodes outside LA reaching a coastal node of the same country through domestic CO2 pipeline candidates: "
            f"{int(ok.reaches_coastal_node.sum())} of {len(ok)}; LA: all 6 inland, no coast (transit). Shortest path km per node in research_inputs/co2_v5/CO2_INLAND_PIPELINE_REACH_S4D1.csv "
            "(S4C-6 integrated build)", "reach_table", "flag", "B", "S4C-6 integrated build", "research_inputs/co2_v5/CO2_INLAND_PIPELINE_REACH_S4D1.csv", rsha, decision_ref="93,35", status="REFERENCE_ONLY")
    src = "Stolaroff J.K. et al. (2021) Transport Cost for Carbon Removal Projects With Biomass and CO2 Storage, Front. Energy Res. 9:639943, doi:10.3389/fenrg.2021.639943"
    reg.add("co2_land_transport_rail_unit_cost", f"Decision 93: CO2 land transport by rail (cryogenic CO2 tank cars), unit cost {RAIL_USD_PER_TKM} $/t-km (Stolaroff 2021 Table 2; "
            f"short-haul < 800 km with > 75 cars, 1.6 x the US national average rail tariff) x {f_usd:.5f} (US${USD_YEAR} -> EUR2020)", rail, "EUR2020/(tCO2 km)", "C", src,
            f"{STOLAROFF_URL} Table 2", psha, sensitivity_low=rail * (1 - SENS), sensitivity_high=rail * (1 + SENS), decision_ref="93")
    reg.add("co2_land_transport_rail_loading_cost", f"Decision 93: rail staging and loading of CO2 at the origin station, {RAIL_LOADING_USD_PER_T} $/t (Stolaroff 2021 section 'Transport of CO2', "
            f"from Gao et al. 2011: 0.88 $/t and Roussanaly et al. 2017: about 1 EUR/t) x {f_usd:.5f}", load, "EUR2020/tCO2", "C", src, f"{STOLAROFF_URL} section Transport of CO2", psha,
            sensitivity_low=load * (1 - SENS), sensitivity_high=load * (1 + SENS), decision_ref="93")
    reg.add("co2_land_transport_truck_unit_cost", f"Alternative (not used in the main run; user decision): CO2 by truck {TRUCK_USD_PER_TKM} $/t-km (Stolaroff 2021 Table 2; 22 t tank trailers, "
            f"ATRI 2017 operating cost 1.16 $/km, empty return, 6 % profit) x {f_usd:.5f}", truck, "EUR2020/(tCO2 km)", "C", src, f"{STOLAROFF_URL} Table 2", psha, decision_ref="93",
            status="REFERENCE_ONLY")
    reg.add("co2_land_transport_crosscheck", "Cross-check quoted in Stolaroff 2021: Gao et al. (2011) rail 77 RMB/t over 600 km at 1.5 Mt/a (= 13 $2018/t incl. 0.88 $/t loading, about "
            "0.020 $/t-km); Roussanaly et al. (2017) rail 4 EUR/t at 50 km and 11 EUR/t at 200 km (about 0.047 EUR/t-km, about 1 EUR/t loading); the main value lies inside this range",
            "within_range", "flag", "B", src, f"{STOLAROFF_URL} section Transport of CO2", psha, decision_ref="93", status="REFERENCE_ONLY")
    reg.add(f"conv_usd{USD_YEAR}_to_eur2020", f"US GDP deflator 2020/{USD_YEAR} ({us20}/{us_y}) x ECB 2020 mean EUR/USD ({fx})", f_usd, f"EUR2020/US${USD_YEAR}", "A",
            "FRED A191RD3A086NBEA; registry fx_usd_to_eur_2020", "research_inputs/registry_v5/sources/A191RD3A086NBEA.csv", sha256(fred), decision_ref="93")
    reg.add("co2_land_route_length_factor", "Decision 93: land route length = great-circle distance x 1.25, the routing factor of the model's pipeline candidates (config "
            "research.s2.pipelines.length_factor; PyPSA-Eur v2025.07.0 config.default.yaml lines 325, 341; equal to registry corridor_length_factor_frozen_base, the median "
            "length / great-circle ratio of the 19 existing cross-border AC lines)", LENGTH_FACTOR, "ratio", "B", "PyPSA-Eur v2025.07.0 config.default.yaml; frozen electric base",
            "lines 325, 341; registry corridor_length_factor_frozen_base", PYPSA_EUR_CONFIG_SHA, decision_ref="93")
    for _, r in tr.iterrows():
        reg.add(f"co2_lao_transit_land_cost_{r.node.replace(' ', '_')}", f"Decision 93: land leg of the Lao transit export from {r.node} to the nearest {r.coast_country} coast at "
                f"({r.coast_point_x}, {r.coast_point_y}) (coastal node {r.coastal_node_at_point}; nearest port record {r.nearest_port_record_to_coast_point}): great-circle "
                f"{r.great_circle_km} km x {LENGTH_FACTOR} = {r.route_km} km x rail {rail:.5f} + loading {load:.4f}; alternative nearest existing sea port {r.alt_sea_port} "
                f"{r.alt_port_route_km} km -> {r.alt_port_land_cost_rail_eur2020_per_t:.2f}; truck alternative {r.land_cost_truck_eur2020_per_t:.2f}",
                float(r.land_cost_rail_eur2020_per_t), "EUR2020/tCO2", "C", src + "; author country_shapes / offshore_shapes", "research_inputs/co2_v5/LAO_TRANSIT_S4D1.csv", tsha,
                node=r.node, country="LA", sensitivity_low=float(r.land_cost_rail_eur2020_per_t) * (1 - SENS), sensitivity_high=float(r.land_cost_rail_eur2020_per_t) * (1 + SENS),
                decision_ref="93")
    reg.add("co2_lao_transit_switch", "research.co2.landlocked_transit values: on (main, decision 93: per LA node one transit export link '<node> co2 transit export extra-ASEAN' from the "
            "captured-CO2 buffer to 'co2 sequestered extra-ASEAN LA', marginal cost = land leg (co2_lao_transit_land_cost_<node>), the store carries the extra-ASEAN unit cost; rail / road "
            "transit treated like the liquid-fuel transit of decision 44 - trade, not cross-border network; both scenarios) | off", "on|off", "flag", "B", "S4D instruction S4D-1 items 3, 4",
            cfg, INSTRUCTION_SHA, decision_ref="93,44", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4d_1.csv")
    summ = dict(f_usd=f_usd, rail_eur2020_per_tkm=rail, loading_eur2020_per_t=load, truck_eur2020_per_tkm=truck, extra_asean_eur2020_per_t=extra, stolaroff_sha256=psha,
                inland_reach={k: int(v) for k, v in ok.reaches_coastal_node.value_counts().items()})
    (OUT / "LAO_TRANSIT_S4D1.json").write_text(json.dumps(dict(summary=summ, transit=tr.to_dict("records"), reach=reach.to_dict("records")), indent=1, default=str))
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
    print(json.dumps(summ, indent=1)); print(reach.to_string()); print(tr.drop(columns=["x", "y"]).T.to_string())


if __name__ == "__main__":
    main()
