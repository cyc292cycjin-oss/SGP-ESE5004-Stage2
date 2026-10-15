"""D1 section 1: LNG import terminals (GEM GGIT LNG Terminals 2025-09) -> nearest network node.

Operating + under-construction import units by country define the existing regasification
capacity; the annual LNG import cap per country is 2.5 x existing (D1 instruction). Proposed
units are registered as candidate sites only (CANDIDATE_ONLY). Energy content: 1 Mtpa LNG =
1e6 t x 48.0 GJ/t (IPCC 2006 default NCV for natural gas) = 13.333 TWh/a.
"""
from __future__ import annotations

import math

from d1_common import (GEM_NAMES, LNG_DIR, REG_DIR, SRC_DIR, UNIT_CONSTANTS, UPSTREAM, Registry,
                       read_csv, sha256, src_sha, write_csv, write_json)

SCRIPT = "scripts_project/d1_lng_terminals.py"
GEM_CSV = "GEM_LNG_TERMINALS_ASEAN_UNITS.csv"
GEM_XLSX_SHA = "20ae2b67"  # prefix as listed in SHA256SUMS.txt (full hash resolved below)
NODES_CSV = "s1_network_nodes_xy.csv"
PORTS = UPSTREAM / "resources" / "baseline-aims-3H-tutorial" / "ports.csv"
CAP_FACTOR = 2.5
MWH_PER_MTPA = 1e6 * UNIT_CONSTANTS["conv_gj_per_t_natural_gas_mass"][0] / 3.6
EXISTING = {"operating", "construction"}


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest(lat, lon, cands):
    best = None
    for c in cands:
        d = haversine(lat, lon, c["lat"], c["lon"])
        if best is None or d < best[1]:
            best = (c, d)
    return best


def full_sha(prefix):
    for line in (SRC_DIR / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.split()[0]
    return prefix


def main():
    units = read_csv(SRC_DIR / GEM_CSV)
    nodes = [dict(bus=r["Bus"], lat=float(r["y"]), lon=float(r["x"]), country=r["country"]) for r in read_csv(SRC_DIR / NODES_CSV)]
    ports = []
    if PORTS.exists():
        for r in read_csv(PORTS):
            if r["country"] in GEM_NAMES.values():
                ports.append(dict(name=r["name"], lat=float(r["y"]), lon=float(r["x"]), country=r["country"]))
    gem_sha = f"GEM-GGIT-LNG-Teminals-2025-09.xlsx:{full_sha(GEM_XLSX_SHA)}; extraction:{src_sha(GEM_CSV)}"
    out_units, caps = [], {}
    for u in units:
        if u["FacilityType"].strip().lower() != "import" or u["Status"] not in {"operating", "construction", "proposed"}:
            continue
        c = GEM_NAMES[u["Country/Area"]]
        cap = float(u["CapacityinMtpa"]) if u["CapacityinMtpa"] not in ("", "nan", "NaN") else None
        lat, lon = float(u["Latitude"]), float(u["Longitude"])
        node, dn = nearest(lat, lon, [n for n in nodes if n["country"] == c])
        port = nearest(lat, lon, [p for p in ports if p["country"] == c]) if ports else None
        rec = dict(country=c, terminal=u["TerminalName"], unit=u["UnitName"], status=u["Status"],
                   capacity_mtpa=cap, capacity_mwh_per_year=None if cap is None else cap * MWH_PER_MTPA,
                   latitude=lat, longitude=lon, accuracy=u["Accuracy"], floating=u["Floating"] in ("1.0", "1"),
                   start_year=u["ActualStartYear"], node=node["bus"], node_distance_km=round(dn, 1),
                   nearest_port=port[0]["name"] if port else "", port_distance_km=round(port[1], 1) if port else None,
                   gem_project_id=u["ProjectID"], gem_unit_id=u["UnitID"], last_updated=u["LastUpdated"])
        out_units.append(rec)
        d = caps.setdefault(c, dict(existing_mtpa=0.0, existing_units=0, units_missing_capacity=0,
                                    proposed_mtpa=0.0, proposed_units=0, nodes=set()))
        if u["Status"] in EXISTING:
            d["existing_units"] += 1
            if cap is None:
                d["units_missing_capacity"] += 1
            else:
                d["existing_mtpa"] += cap
                d["nodes"].add(node["bus"])
        else:
            d["proposed_units"] += 1
            if cap is None:
                d["units_missing_capacity"] += 1
            else:
                d["proposed_mtpa"] += cap
    reg = Registry(SCRIPT)
    cap_rows = []
    for c in sorted(set(GEM_NAMES.values())):
        d = caps.get(c, dict(existing_mtpa=0.0, existing_units=0, units_missing_capacity=0, proposed_mtpa=0.0,
                             proposed_units=0, nodes=set()))
        cap_mwh = CAP_FACTOR * d["existing_mtpa"] * MWH_PER_MTPA
        cap_rows.append(dict(country=c, existing_mtpa=d["existing_mtpa"], existing_units=d["existing_units"],
                             existing_mwh_per_year=d["existing_mtpa"] * MWH_PER_MTPA, cap_factor=CAP_FACTOR,
                             import_cap_mwh_per_year=cap_mwh, proposed_mtpa=d["proposed_mtpa"],
                             proposed_units=d["proposed_units"], units_missing_capacity=d["units_missing_capacity"],
                             nodes=";".join(sorted(d["nodes"]))))
        status = "REGISTERED" if d["existing_mtpa"] > 0 else "SOURCE_ZERO"
        reg.add(f"lng_existing_capacity_{c}", f"{c} LNG import regasification capacity, operating + under construction "
                f"({d['existing_units']} units, {d['units_missing_capacity']} unit(s) without capacity in GEM)",
                d["existing_mtpa"], "Mtpa", "A", "GEM Global Gas Infrastructure Tracker, LNG Terminals 2025-09",
                "sheet LNG terminals, FacilityType=import, Status in {operating, construction}", gem_sha, country=c,
                node=";".join(sorted(d["nodes"])), decision_ref="D1-1 LNG", status=status)
        reg.add(f"lng_import_cap_{c}", f"{c} annual LNG import cap = {CAP_FACTOR} x existing capacity x "
                f"{MWH_PER_MTPA:.4g} MWh/Mtpa (48.0 GJ/t NCV)", cap_mwh, "MWh/a", "B",
                "derived from lng_existing_capacity_" + c + " and conv_gj_per_t_natural_gas_mass",
                f"{CAP_FACTOR} x Mtpa x 1e6 t x 48.0 GJ/t / 3.6", gem_sha, country=c,
                node=";".join(sorted(d["nodes"])), sensitivity_low=d["existing_mtpa"] * MWH_PER_MTPA,
                sensitivity_high=cap_mwh * 50.4 / 48.0, decision_ref="D1-1 LNG", status=status)
    for r in out_units:
        if r["status"] == "proposed":
            reg.add(f"lng_candidate_{r['country']}_{r['gem_unit_id']}",
                    f"{r['country']} proposed LNG import unit {r['terminal']} {r['unit']} (candidate site only)",
                    r["capacity_mtpa"], "Mtpa", "A", "GEM GGIT LNG Terminals 2025-09", f"UnitID {r['gem_unit_id']}",
                    gem_sha, country=r["country"], node=r["node"], decision_ref="D1-1 LNG",
                    status="CANDIDATE_ONLY" if r["capacity_mtpa"] is not None else "DATA_PENDING")
    reg.add("lng_mwh_per_mtpa", "Energy content of 1 Mtpa LNG on an NCV basis (1e6 t x 48.0 GJ/t / 3.6)",
            MWH_PER_MTPA, "MWh/(Mtpa*a)", "B", "IPCC 2006 Vol.2 Ch.1 Table 1.2 (natural gas 48.0, 46.5-50.4 TJ/Gg)",
            "Table 1.2", src_sha("IPCC_2006_Vol2_Ch1_Introduction.pdf"), sensitivity_low=1e6 * 46.5 / 3.6,
            sensitivity_high=1e6 * 50.4 / 3.6)
    reg.add("lng_import_cap_factor", "Import cap multiplier on existing regasification capacity (D1 instruction)",
            CAP_FACTOR, "ratio", "C", "D1_DATA_INSTRUCTION.md section 1", "LNG terminals bullet", src_sha(GEM_CSV),
            sensitivity_low=1.0, sensitivity_high=5.0, decision_ref="D1-1 LNG")
    cols = list(out_units[0].keys())
    write_csv(sorted(out_units, key=lambda r: (r["country"], r["status"], r["terminal"], r["unit"])),
              LNG_DIR / "LNG_IMPORT_TERMINALS_GEM_2025.csv", cols)
    write_csv(cap_rows, LNG_DIR / "LNG_IMPORT_CAPS_BY_COUNTRY.csv", list(cap_rows[0].keys()))
    reg.write(REG_DIR / "fragments" / "lng_terminals.csv")
    write_json(dict(script=SCRIPT, mwh_per_mtpa=MWH_PER_MTPA, cap_factor=CAP_FACTOR, nodes_source=NODES_CSV,
                    nodes_sha=src_sha(NODES_CSV), ports_source=str(PORTS), ports_sha=sha256(PORTS) if PORTS.exists() else None,
                    caps=cap_rows, units=len(out_units)), REG_DIR / "fragments" / "lng_terminals.json")
    for r in cap_rows:
        print(f"{r['country']}: existing {r['existing_mtpa']:.2f} Mtpa ({r['existing_units']} units, missing cap {r['units_missing_capacity']}) "
              f"-> cap {r['import_cap_mwh_per_year']:.3e} MWh/a; proposed {r['proposed_mtpa']:.2f} Mtpa; nodes {r['nodes']}")


if __name__ == "__main__":
    main()
