"""D1 section 1: domestic fossil fuel production caps from UNSD 2019 energy statistics.

Annual supply cap per country and carrier (MWh NCV) = 2019 primary production:
  coal = Hard coal + Brown coal production (UNSD aggregates; anthracite/lignite are subsets),
  gas  = Natural gas gross production (TJ GCV) x 0.90 (UNSD GCV->NCV) -- gross includes
         flared/re-injected gas, so this is an upper bound; UNSD files hold no marketed row,
  oil  = Conventional crude oil + Natural gas liquids production.
Countries without a production transaction get a SOURCE_ZERO row (supply only via
terminals/ports/pipelines). Same price as imports (D1 instruction).
"""
from __future__ import annotations

import glob

import pandas as pd

from d1_common import ASEAN, REG_DIR, UNIT_CONSTANTS, UNSD_NAMES, UPSTREAM, Registry, sha256, write_csv, write_json

SCRIPT = "scripts_project/d1_fossil_production.py"
UNSD_DIR = UPSTREAM / "data" / "demand" / "unsd" / "data"
GJ = {"Hard coal": UNIT_CONSTANTS["conv_gj_per_t_hardcoal_ncv"][0],
      "Brown coal": UNIT_CONSTANTS["conv_gj_per_t_browncoal_ncv"][0],
      "Conventional crude oil": UNIT_CONSTANTS["conv_gj_per_t_crude_ncv"][0],
      "Natural gas liquids": UNIT_CONSTANTS["conv_gj_per_t_ngl_ncv"][0]}
GCV_TO_NCV = UNIT_CONSTANTS["conv_gas_gcv_to_ncv"][0]
WANTED = {("Hard coal", "production"): "coal", ("Brown coal", "production"): "coal",
          ("Conventional crude oil", "production"): "oil", ("Natural gas liquids", "production"): "oil",
          ("Natural gas", "gross production"): "gas"}


def load_unsd_2019():
    rows = []
    for f in sorted(glob.glob(str(UNSD_DIR / "UNdata_Export_*.txt"))):
        d = pd.read_csv(f, sep=";", dtype=str, low_memory=False)
        d = d[d["Country or Area"].isin(UNSD_NAMES) & (d["Year"] == "2019")]
        if len(d):
            d = d.assign(file=f.split("/")[-1], sha=sha256(f))
            rows.append(d)
    u = pd.concat(rows, ignore_index=True)
    u["ISO"] = u["Country or Area"].map(UNSD_NAMES)
    parts = u["Commodity - Transaction"].str.split(" - ", n=1, expand=True)
    u["commodity"] = parts[0].str.strip()
    u["transaction"] = parts[1].str.strip().str.lower()
    return u


def main():
    u = load_unsd_2019()
    sel = u[[(c, t) in WANTED for c, t in zip(u.commodity, u.transaction)]].copy()
    sel["carrier"] = [WANTED[(c, t)] for c, t in zip(sel.commodity, sel.transaction)]
    recs = []
    for _, r in sel.iterrows():
        q = float(r.Quantity)
        if r.commodity == "Natural gas":
            assert r.Unit.strip() == "Terajoules", r.Unit
            mwh = q * GCV_TO_NCV / 0.0036
            conv = "TJ GCV x 0.90 / 0.0036"
        else:
            assert r.Unit.strip().startswith("Metric tons,  thousand") or "thousand" in r.Unit, r.Unit
            mwh = q * 1e3 * GJ[r.commodity] / 3.6
            conv = f"kt x 1e3 x {GJ[r.commodity]} GJ/t / 3.6"
        recs.append(dict(country=r.ISO, carrier=r.carrier, commodity=r.commodity, transaction=r.transaction,
                         quantity=q, unit=r.Unit.strip(), mwh_ncv=mwh, conversion=conv, source_file=r.file,
                         source_sha256=r.sha, footnote=r.get("Quantity Footnotes", "")))
    df = pd.DataFrame(recs)
    reg = Registry(SCRIPT)
    for _, r in df.iterrows():
        key = r.commodity.lower().replace(" ", "_")
        reg.add(f"fossil_production_2019_{r.country}_{key}", f"{r.country} UNSD 2019 {r.commodity} - {r.transaction}",
                r.quantity, r.unit, "A", f"UNSD Energy Statistics Database export {r.source_file}",
                f"{r['Country or Area'] if 'Country or Area' in r else r.country}; {r.commodity} - {r.transaction}; year 2019",
                r.source_sha256, country=r.country, decision_ref="D1-1 production caps")
    caps = []
    for c in ASEAN:
        for carrier in ["coal", "gas", "oil"]:
            d = df[(df.country == c) & (df.carrier == carrier)]
            mwh = float(d.mwh_ncv.sum())
            comps = "; ".join(f"{x.commodity} {x.quantity:g} {x.unit}" for _, x in d.iterrows()) or "no UNSD production transaction"
            caps.append(dict(country=c, carrier=carrier, cap_mwh_per_year=mwh, components=comps,
                             basis="gross production (upper bound)" if carrier == "gas" and mwh > 0 else "production",
                             source_files=";".join(sorted(set(d.source_file))) if len(d) else ""))
            sha = ";".join(f"{f}:{s}" for f, s in sorted(set(zip(d.source_file, d.source_sha256)))) if len(d) else "n/a"
            reg.add(f"fossil_production_cap_{carrier}_{c}", f"{c} annual domestic {carrier} supply cap = UNSD 2019 "
                    f"production ({comps}); NCV basis", mwh, "MWh/a", "B",
                    "UNSD Energy Statistics Database 2019 (pypsa-asean/data/demand/unsd/data)",
                    "production rows listed in fossil_production_2019_* ; conversion factors conv_*", sha, country=c,
                    sensitivity_low=None, sensitivity_high=None, decision_ref="D1-1 production caps",
                    status="REGISTERED" if mwh > 0 else "SOURCE_ZERO")
    reg.add("fossil_production_gas_basis", "UNSD natural gas files contain only 'Gross production' (no marketed "
            "production row); gross includes flared and re-injected gas -> caps are upper bounds", "gross_production",
            "basis", "A", "UNSD export transaction list", "natural gas transactions: gross production only",
            ";".join(sorted(set(df.source_sha256))), decision_ref="D1-1 production caps")
    write_csv(sorted(recs, key=lambda r: (r["country"], r["carrier"], r["commodity"])),
              REG_DIR / "FOSSIL_PRODUCTION_2019_UNSD.csv", list(recs[0].keys()))
    write_csv(caps, REG_DIR / "FOSSIL_PRODUCTION_CAPS_2050.csv", list(caps[0].keys()))
    reg.write(REG_DIR / "fragments" / "fossil_production.csv")
    write_json(dict(script=SCRIPT, rows=len(recs), caps=caps), REG_DIR / "fragments" / "fossil_production.json")
    for r in caps:
        if r["cap_mwh_per_year"] > 0:
            print(f"{r['country']} {r['carrier']}: {r['cap_mwh_per_year']/1e6:10.2f} TWh/a  [{r['components']}]")


if __name__ == "__main__":
    main()
