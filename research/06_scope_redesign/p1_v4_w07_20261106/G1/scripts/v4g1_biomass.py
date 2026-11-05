"""V4 W07 G1 step 7 (Malaysia): biomass definitions and the closed-loop rule (decisions 206 items 1 and 3).

    python scripts/v4g1_biomass.py        (WSL pypsa-earth python; after v4g1_base.py)

Checks: every UNSD 2019 MY biomass commodity and flow (UNdata export = model source, and the SDMX response of this session), series 2005-2022 with
'Estimate' footnotes and household / industry shifts; whether UNSD reports black liquor (5140) or other vegetal material and residues (5150) and in
which flows; FAOSTAT FO wood fuel (narrower definition) and QCL oil palm fruit / palm oil / sugar cane; palm-oil-mill residues by the IRENA 2022 mass
balance (fibre, shell, empty fruit bunches) at 15 GJ/t (IRENA 2017 residue convention, as S2) as the closed-loop quantity outside T_v2; NEB 2019
industry biomass and self-generation biomass. Outputs tables/MY_BIOMASS_CHECK.csv (A6 schema), MY_BIOMASS_SERIES.csv, tables/_biomass_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g1_common as cm   # noqa: E402

OUT = cm.G1 / "tables"
MASS = dict(fibre=0.144, shell=0.064, efb=0.21)   # t per t FFB, IRENA 2022 p.40 box 4 (quoting Eriza 2010), as S2 section 2.4
GJ_T_RESIDUE = 15.0                               # IRENA 2017 residue convention (moisture not stated), as S2


def main():
    ev = cm.Ev("biomass")
    base = json.loads((OUT / "_base_evidence.json").read_text())["extra"]; neb = base["neb_checks"]
    conv = cm.frozen_conv()
    U, notes = cm.unsd_export()
    BIO = ["Fuelwood", "Bagasse", "Charcoal", "Biodiesel", "Biogases", "Black liquor", "Other vegetal material and residues", "Animal waste", "Biogasoline"]
    b = U[U.commodity.str.lower().isin([x.lower() for x in BIO])].copy()
    S = pd.read_csv(cm.G1 / "sdmx/MY_SDMX_OBS.csv", dtype={"commodity_code": str, "transaction_code": str})
    sb = S[S.commodity_code.isin(["5110", "5120", "5140", "5150", "5160"]) | S.commodity.isin(["Biodiesel", "Biogases"])]
    # ---- 2019 rows
    rows = []
    for r in b[b.y == 2019].sort_values(["commodity", "transaction"]).itertuples():
        f = conv.get(r.commodity, None)
        tw = r.q / 3.6e3 if "terajoule" in r.Unit.lower() else (r.q * float(f) if f is not None else np.nan)
        rows.append(dict(dataset="UNdata export (model)", commodity=r.commodity, flow=r.transaction, value_2019=r.q, unit=r.Unit, twh=tw, footnote=r.footnote))
    for r in sb[sb.year == 2019].drop_duplicates(subset=["commodity_code", "transaction_code"]).itertuples():
        tj = r.value if r.unit == "TJ" else r.value * (r.conversion_factor or np.nan)
        rows.append(dict(dataset="SDMX 2019", commodity=r.commodity, flow=r.transaction, value_2019=r.value, unit=r.unit, twh=tj / 3.6e3, footnote=r.obs_status))
    R19 = pd.DataFrame(rows)
    # ---- series
    ser = []
    for com, tr in (("Bagasse", "Consumption by manufacturing, construction and non-fuel industry"), ("Fuelwood", "Consumption by households"), ("Fuelwood", "Production"),
                    ("Charcoal", "Production"), ("Biogases", "Production")):
        z = U[(U.commodity.str.lower() == com.lower()) & (U.transaction.str.lower() == tr.lower()) & U.y.between(2005, 2022)].sort_values("y").drop_duplicates("y")
        for r in z.itertuples():
            ser.append(dict(source="UNdata export", commodity=com, flow=tr, year=r.y, value=r.q, unit=r.Unit, footnote=r.footnote))
    for r in S[(S.commodity_code == "5150")].sort_values(["transaction_code", "year"]).itertuples():
        ser.append(dict(source="SDMX", commodity=r.commodity, flow=r.transaction, year=r.year, value=r.value, unit=r.unit, footnote=r.obs_status))
    FO, QCL = cm.fao("FO"), cm.fao("QCL")
    fo = FO[(FO.Area == cm.AREA) & FO.Item.str.contains("Wood fuel|Wood residues|Wood chips|pellets", case=False)]
    for r in fo[fo.Element.isin(["Production", "Import quantity", "Export quantity"])].sort_values(["Item", "Element", "year"]).itertuples():
        ser.append(dict(source="FAOSTAT FO", commodity=r.Item, flow=r.Element, year=r.year, value=r.value, unit=r.Unit, footnote=r.flag))
    qc = QCL[(QCL.Area == cm.AREA) & QCL.Item.isin(["Oil palm fruit", "Palm oil", "Palm kernels", "Sugar cane"]) & QCL.Element.eq("Production")]
    for r in qc.sort_values(["Item", "year"]).itertuples():
        ser.append(dict(source="FAOSTAT QCL", commodity=r.Item, flow=r.Element, year=r.year, value=r.value, unit=r.Unit, footnote=r.flag))
    SER = pd.DataFrame(ser); SER.to_csv(OUT / "MY_BIOMASS_SERIES.csv", index=False, float_format="%.10g")
    gv = lambda src, com, flow, y: (lambda z: float(z.value.iloc[0]) if len(z) else np.nan)(SER[(SER.source == src) & (SER.commodity == com) & (SER.flow == flow) & (SER.year == y)])
    gf = lambda src, com, flow, y: (lambda z: str(z.footnote.iloc[0]) if len(z) else "")(SER[(SER.source == src) & (SER.commodity == com) & (SER.flow == flow) & (SER.year == y)])
    # ---- FAOSTAT wood fuel and palm
    wf_items = [i for i in fo.Item.unique() if i.lower().startswith("wood fuel")]
    wf19 = float(np.nansum([gv("FAOSTAT FO", i, "Production", 2019) for i in wf_items if i != "Wood fuel"]))   # coniferous + non-coniferous
    ev.put("bio.fao_wood_fuel_items", ";".join(f"{i}:{gv('FAOSTAT FO', i, 'Production', 2019)}{gf('FAOSTAT FO', i, 'Production', 2019)}" for i in wf_items), "-", "FAOSTAT FO 2019", "VERIFIED", "B")
    ffb19, ffb_flag = gv("FAOSTAT QCL", "Oil palm fruit", "Production", 2019), gf("FAOSTAT QCL", "Oil palm fruit", "Production", 2019)
    cpo19, cpo_flag = gv("FAOSTAT QCL", "Palm oil", "Production", 2019), gf("FAOSTAT QCL", "Palm oil", "Production", 2019)
    cane19 = gv("FAOSTAT QCL", "Sugar cane", "Production", 2019)
    res = {k: ffb19 * v for k, v in MASS.items()}
    e_res = {k: v * GJ_T_RESIDUE / 3.6e6 for k, v in res.items()}   # TWh
    fw_prod_e = gv("UNdata export", "Fuelwood", "Production", 2019)
    v5150_prod = float(S[(S.commodity_code == "5150") & (S.year == 2019) & (S.transaction.str.lower() == "production")].value.iloc[0]) / 3.6e3
    v5150_auto = float(S[(S.commodity_code == "5150") & (S.year == 2019) & S.transaction.str.contains("autoproducers")].value.iloc[0]) / 3.6e3
    first5150 = int(S[(S.commodity_code == "5150") & (S.transaction.str.lower() == "production")].year.min()) if len(S[S.commodity_code == "5150"]) else None
    bag_ind = R19[(R19.dataset.str.startswith("UNdata")) & (R19.commodity == "Bagasse") & R19.flow.str.lower().str.startswith("consumption by manufacturing")].twh.iloc[0]
    # ---- A6 table
    C = [dict(commodity="Bagasse (5120)", flow="industry n.e.s. (UNdata export = model)", value_2019=f"5.8 kt = {bag_ind:.4f} TWh",
              series_note="Estimate every year; 179 kt (2006) -> 2.6-8.5 kt (2014-2019): small cane sector", faostat_compare=f"FAOSTAT sugar cane 2019 {cane19:,.0f} t",
              proposed_main="keep (in T_v2, 0.012 TWh)", proposed_sensitivity="none"),
         dict(commodity="Fuelwood (5110)", flow="households (Estimate); no industry flow", value_2019=f"export {gv('UNdata export', 'Fuelwood', 'Consumption by households', 2019):,.1f} km3 / SDMX 2,329.7 km3",
              series_note="no industry fuelwood in any year 2005-2022; household flow Estimate; export and SDMX versions differ (2,275.3 vs 2,329.7 km3; charcoal plants 140.4 vs 86.5 km3)",
              faostat_compare=f"FAOSTAT wood fuel production 2019 {wf19:,.0f} m3 vs UNSD production {fw_prod_e:,.1f} km3 (ratio {fw_prod_e * 1e3 / wf19:.2f})",
              proposed_main="no industry fuelwood: nothing to change", proposed_sensitivity="none"),
         dict(commodity="Black liquor (5140)", flow="not reported (export and SDMX)", value_2019="0", series_note="never reported 2010-2022",
              faostat_compare="FAOSTAT chemical pulp 131 kt (2015 A, carried forward)", proposed_main="closed-loop: pulp black liquor outside T_v2 (decision 206 item 3)", proposed_sensitivity="none"),
         dict(commodity="Other vegetal material and residues (5150)", flow="production; transformation in electricity plants (autoproducers E, main activity E); no final consumption",
              value_2019=f"production {v5150_prod:.3f} TWh; autoproducers {v5150_auto:.3f} TWh",
              series_note=f"SDMX only (first year {first5150}); absent from the UNdata export used by the model (coverage gap, W11 / W12 item 4)",
              faostat_compare=f"palm residues 2019 (FFB {ffb19 / 1e6:.1f} Mt {ffb_flag} x IRENA 2022): fibre {e_res['fibre']:.1f}, shell {e_res['shell']:.1f}, EFB {e_res['efb']:.1f} TWh at 15 GJ/t",
              proposed_main="outside T_v2: reported only as power-plant fuel; mill boiler steam from fibre / shell is closed-loop (not reported, not in T_v2)",
              proposed_sensitivity="W08: add 5150 autoproducer fuel to the supply-side power accounts (not T_v2)"),
         dict(commodity="Charcoal (5160)", flow="households, other (commerce); no industry", value_2019="5.882 kt (other, Estimate)", series_note="", faostat_compare="",
              proposed_main="no industry charcoal", proposed_sensitivity="none"),
         dict(commodity="Biodiesel", flow="road only", value_2019="737.69 kt", series_note="", faostat_compare="", proposed_main="not industry", proposed_sensitivity="none"),
         dict(commodity="Biogases", flow="autoproducer electricity only", value_2019="4,425.2 TJ = 1.229 TWh", series_note="", faostat_compare="",
              proposed_main="transformation (not T_v2); palm-oil-mill effluent biogas (INFERENCE)", proposed_sensitivity="none"),
         dict(commodity="NEB 2019 biomass", flow="industry 0 ktoe; self-generation input 136 ktoe (525 GWh); co-generation biomass 128.6 MW, self-generation biomass 241.3 MW",
              value_2019=f"self-generation input {neb['selfgen_biomass_input_twh']:.3f} TWh", series_note="NEB: industry has no biomass column value",
              faostat_compare="", proposed_main="consistent with UNSD: no industrial biomass final consumption", proposed_sensitivity="none")]
    CB = pd.DataFrame(C); CB.insert(0, "country", cm.CC)
    CB.to_csv(OUT / "MY_BIOMASS_CHECK.csv", index=False)
    R19.to_csv(OUT / "MY_BIOMASS_UNSD_2019.csv", index=False, float_format="%.10g")
    for k, v in dict(ffb_2019_t=ffb19, cpo_2019_t=cpo19, oer=cpo19 / ffb19, sugar_cane_2019_t=cane19, fao_wood_fuel_2019_m3=wf19, unsd_fuelwood_production_2019_km3=fw_prod_e,
                     unsd_5150_production_2019_twh=v5150_prod, unsd_5150_autoproducer_2019_twh=v5150_auto, bagasse_industry_2019_twh=bag_ind,
                     **{f"palm_{k}_2019_t": v for k, v in res.items()}, **{f"palm_{k}_2019_twh": v for k, v in e_res.items()}).items():
        ev.put(f"bio.{k}", v, "t" if k.endswith("_t") else ("m3" if k.endswith("m3") else ("km3" if k.endswith("km3") else ("TWh" if k.endswith("twh") else "-"))),
               "UNdata export / UNSD SDMX / FAOSTAT FO, QCL / IRENA 2022 mass balance x 15 GJ/t", "VERIFIED" if not k.startswith("palm") and k != "oer" else "INFERENCE", "B" if not k.startswith("palm") else "C")
    ev.put("bio.closed_loop_palm_low_twh", e_res["fibre"], "TWh", "fibre only (mill boilers)", "INFERENCE", "C")
    ev.put("bio.closed_loop_palm_high_twh", e_res["fibre"] + e_res["shell"], "TWh", "fibre + shell (shell partly exported, upper bound)", "INFERENCE", "C")
    ev.put("bio.t_v2_change", 0.0, "TWh", "no MY industrial biomass to re-classify; palm residues closed-loop", "PROPOSED", "B")
    ev.extra["footnote_legend"] = notes
    ev.write(OUT / "_biomass_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120); pd.set_option("display.max_rows", 100)
    print(R19.to_string()); print(CB.T.to_string())
    print(SER[SER.source.isin(["SDMX"])].to_string())
    print(json.dumps(dict(ffb=ffb19, cpo=cpo19, cane=cane19, wf19=wf19, res=res, e_res=e_res), indent=1))


if __name__ == "__main__":
    main()
