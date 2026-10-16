"""S4C-1 item 5 (S4C supplement 01, ledger L18, decision 16): geometric subsea share of every transport corridor.

PyPSA-Eur v2025.07.0 computes the underwater fraction of a link as the share of its route inside the offshore shape:
scripts/base_network.py lines 603-614 (_set_links_underwater_fraction: links.intersection(offshore_shape).length / links.length, with
offshore_shape = union of resources/offshore_shapes.geojson); prepare_sector_network.py create_network_topology (lines 368-420 of the
registered copy) carries it to the H2 / CO2 / gas candidates of the same node pair; add_electricity.py lines 491-502 price DC links with
(1 - uw) x HVDC overhead + uw x HVDC submarine (+ inverter pair). [read-only view of base_network.py v2025.07.0, SHA256 9a2ea2fa...]

Here the route of a corridor is the great-circle path between the two node locations (the same path whose length x 1.25 is the
corridor length in the model), sampled every ~0.5 km; each sample is classified against the author shapes of the pypsa-asean chain
(resources/baseline-aims-3H-tutorial/shapes/offshore_shapes.geojson = offshore (EEZ) areas, country_shapes.geojson = land), so
  subsea_share = share of samples inside the offshore union (PyPSA-Eur definition, main)
  not_land_share = 1 - share of samples inside the land union (cross-check), gap_share = samples in neither shape.
A corridor whose gap share exceeds 5 % cannot be classified by these shapes (stop rule of the supplement: report).

Inputs: the S4C-0 integrated build (all lines, DC / B2B links, H2 / CO2 / gas pipeline links incl. connectivity upgrades and the 2025
gas stock; locations = n.buses.location), research_inputs/corridors/cross_border_corridors.csv. Common-sense checks of the supplement
(item 4) are added for node pairs that carry no model candidate (marked candidate=False).

    python scripts_project/s4c_1_subsea_shares.py --network results_project/s4c/build_s4c0/integrated/integrated_2920_3h_unsolved.nc
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pypsa
import shapely
from pyproj import Geod

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/shapes")
OUT = ROOT / "research_inputs" / "corridors"
STEP_KM = 0.5
GAP_STOP = 0.05
CHECKS = [   # supplement item 4: obvious subsea and obvious land corridors (node pairs chosen as the nearest nodes on each side)
    ("SG2 0", "ID_Sumatra2 0", "subsea", "SG - ID Batam (Gresik-Batam-Singapore gas pipeline landfall node)"),
    ("MY_Peninsular2 1", "SG2 0", "mostly land (Johor causeway)", "MY peninsular - SG (existing AC line)"),
    ("MY_Peninsular22 0", "TH21 0", "land", "MY - TH (existing HVDC / TTM gas)"),
    ("LA2 0", "TH2 1", "land (Mekong crossing)", "LA - TH"),
    ("KH2 0", "VN2 0", "land", "KH - VN"),
]
EXTRA_CHECK_PAIRS = [   # no model candidate: pairs for the common-sense check of the method only
    ("MY_Peninsular2 1", "MY_Sarawak4 0", "subsea", "MY peninsular - Sarawak (no candidate)"),
    ("MY_Peninsular2 1", "MY_Sabah4 0", "subsea", "MY peninsular - Sabah (no candidate)"),
    ("PH_Mindanao6 0", "MY_Sabah4 0", "subsea", "PH Mindanao - MY Sabah (no candidate)"),
    ("ID_Sumatra2 0", "MY_Peninsular2 1", "subsea", "ID Sumatra - MY peninsular (no candidate)"),
]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def classify(geod, land, off, x0, y0, x1, y1):
    dist_m = geod.inv(x0, y0, x1, y1)[2]
    k = max(int(np.ceil(dist_m / 1e3 / STEP_KM)), 2)
    pts = np.array([(x0, y0)] + geod.npts(x0, y0, x1, y1, k - 1) + [(x1, y1)])
    mid = (pts[1:] + pts[:-1]) / 2   # segment midpoints, equal geodesic spacing
    in_off = shapely.contains_xy(off, mid[:, 0], mid[:, 1]); in_land = shapely.contains_xy(land, mid[:, 0], mid[:, 1])
    return dict(great_circle_km=dist_m / 1e3, samples=int(len(mid)), subsea_share=float(in_off.mean()), not_land_share=float(1 - in_land.mean()),
                gap_share=float((~in_off & ~in_land).mean()), overlap_share=float((in_off & in_land).mean()))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); a = ap.parse_args()
    n = pypsa.Network(str(a.network)); b = n.buses
    land_gdf = gpd.read_file(AUTHOR / "country_shapes.geojson"); off_gdf = gpd.read_file(AUTHOR / "offshore_shapes.geojson")
    land = land_gdf.union_all(); off = off_gdf.union_all(); shapely.prepare(land); shapely.prepare(off)
    geod = Geod(ellps="WGS84")

    suffixes = (" gas", " H2", " co2 stored", " oil")

    def loc(bus):
        """Node location of a bus: n.buses.location, else the bus name without its carrier suffix (gas buses of the S3 layer carry no
        location and no coordinates), else the bus itself; the result must have coordinates."""
        l = str(b.at[bus, "location"]) if "location" in b and str(b.at[bus, "location"]) not in ("", "nan") else bus
        if l not in b.index or (float(b.at[l, "x"]) == 0.0 and float(b.at[l, "y"]) == 0.0):
            for s in suffixes:
                if bus.endswith(s) and bus[: -len(s)] in b.index:
                    l = bus[: -len(s)]; break
        if l not in b.index or (float(b.at[l, "x"]) == 0.0 and float(b.at[l, "y"]) == 0.0):
            raise ValueError(f"no coordinates for the location of bus {bus!r}")
        return l

    comps = []
    for name, z in n.lines.iterrows():
        comps.append(dict(component="Line", name=str(name), carrier="AC", bus0=z.bus0, bus1=z.bus1, length_km=float(z.length), kind=""))
    for name, z in n.links[n.links.carrier.isin(["DC", "B2B", "H2 pipeline", "CO2 pipeline", "gas pipeline"])].iterrows():
        comps.append(dict(component="Link", name=str(name), carrier=z.carrier, bus0=z.bus0, bus1=z.bus1, length_km=float(z.length), kind=str(z.get("gas_pipeline_kind", "") or "")))
    pairs = {}
    for c in comps:
        l0, l1 = loc(c["bus0"]), loc(c["bus1"]); key = tuple(sorted((l0, l1)))
        c.update(loc0=key[0], loc1=key[1])
        if key not in pairs and key[0] != key[1]:
            pairs[key] = classify(geod, land, off, float(b.at[key[0], "x"]), float(b.at[key[0], "y"]), float(b.at[key[1], "x"]), float(b.at[key[1], "y"]))
    rows = []
    for (l0, l1), v in sorted(pairs.items()):
        used = [c for c in comps if (c["loc0"], c["loc1"]) == (l0, l1)]
        c0, c1 = str(b.at[l0, "country"]), str(b.at[l1, "country"])
        rows.append(dict(loc0=l0, loc1=l1, country0=c0, country1=c1, cross_border=c0 != c1, candidate=True, **v,
                         components=";".join(sorted({f"{c['component']}:{c['carrier']}" for c in used})), n_components=len(used),
                         names=";".join(sorted(c["name"] for c in used))[:400], check_expectation="", check_label=""))
    t = pd.DataFrame(rows)
    for l0, l1, expect, label in CHECKS + EXTRA_CHECK_PAIRS:
        key = tuple(sorted((l0, l1)))
        m = (t.loc0 == key[0]) & (t.loc1 == key[1])
        if m.any():
            t.loc[m, ["check_expectation", "check_label"]] = [expect, label]
        else:
            v = classify(geod, land, off, float(b.at[key[0], "x"]), float(b.at[key[0], "y"]), float(b.at[key[1], "x"]), float(b.at[key[1], "y"]))
            t = pd.concat([t, pd.DataFrame([dict(loc0=key[0], loc1=key[1], country0=str(b.at[key[0], "country"]), country1=str(b.at[key[1], "country"]),
                                                cross_border=b.at[key[0], "country"] != b.at[key[1], "country"], candidate=False, **v, components="", n_components=0, names="",
                                                check_expectation=expect, check_label=label)])], ignore_index=True)
    # corridor table rows (supplement item 4: all cross-border corridors listed)
    cor = pd.read_csv(ROOT / "research_inputs/corridors/cross_border_corridors.csv")
    cor_rows = []
    for r in cor.itertuples():
        key = tuple(sorted((loc(str(r[1])), loc(str(r[2])))))
        m = t[(t.loc0 == key[0]) & (t.loc1 == key[1])]
        cor_rows.append(dict(from_=getattr(r, "_1", None) or r[1], to=r[2], carrier=r.carrier, component_type=r.component_type, component=r.component, status=r.status,
                             subsea_share_table=float(r.subsea_share), subsea_share_geometric=(float(m.subsea_share.iloc[0]) if len(m) else np.nan),
                             gap_share=(float(m.gap_share.iloc[0]) if len(m) else np.nan)))
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "SUBSEA_SHARE_S4C1.csv", index=False)
    pd.DataFrame(cor_rows).rename(columns={"from_": "from"}).to_csv(OUT / "CORRIDOR_SUBSEA_SHARE_S4C1.csv", index=False)
    stop = t[t.gap_share > GAP_STOP]
    ev = dict(network=str(a.network), network_sha256=sha(a.network), shapes=dict(country_shapes=sha(AUTHOR / "country_shapes.geojson"), offshore_shapes=sha(AUTHOR / "offshore_shapes.geojson")),
              step_km=STEP_KM, gap_stop=GAP_STOP, pairs=int(len(t)), candidate_pairs=int(t.candidate.sum()), cross_border_pairs=int((t.candidate & t.cross_border).sum()),
              pairs_with_subsea_gt_0_05=int(((t.subsea_share > 0.05) & t.candidate).sum()), max_gap=float(t.gap_share.max()),
              stop_pairs=stop[["loc0", "loc1", "gap_share"]].to_dict("records"),
              checks=t[t.check_label != ""][["check_label", "check_expectation", "candidate", "great_circle_km", "subsea_share", "not_land_share", "gap_share"]].to_dict("records"))
    (OUT / "SUBSEA_SHARE_S4C1_EVIDENCE.json").write_text(json.dumps(ev, indent=1, default=str) + "\n")
    pd.set_option("display.width", 250)
    print(t[t.check_label != ""][["check_label", "candidate", "great_circle_km", "subsea_share", "not_land_share", "gap_share"]].round(3).to_string())
    print(t[t.candidate & (t.subsea_share > 0.05)].sort_values("subsea_share", ascending=False)[["loc0", "loc1", "great_circle_km", "subsea_share", "not_land_share", "gap_share", "components"]].round(3).to_string())
    print(json.dumps({k: v for k, v in ev.items() if k not in ("checks",)}, default=str)[:1500])


if __name__ == "__main__":
    main()
