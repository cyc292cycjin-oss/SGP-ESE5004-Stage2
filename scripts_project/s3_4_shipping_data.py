"""S3-4 (decision 10, D1 section 4): shipping demand registry fragment.

Demand = D1 table rows DomesticShippingFuel (Transport) and InternationalShippingBunker (outside TFEC, switch research.s2.demand.international_bunkers
shared with aviation) in oil-equivalent MWh; 2050 fuel shares from the PyPSA-Eur config registered in D1 (methanol 1 / hydrogen 0 / oil 0);
methanol energy = oil-equivalent x shipping_oil_efficiency 0.40 / shipping_methanol_efficiency 0.46 (config lines 636/635, add_shipping lines
5195-5200); CO2 at use = 1/MWh_MeOH_per_tCO2 = technology-data methanol CO2 intensity 0.2482 t/MWh in the consuming country (lines 5218-5227);
origin-neutral treatment in S3-5 (decision 64).

    python scripts_project/s3_4_shipping_data.py
"""
from __future__ import annotations

import pandas as pd

from d1_common import ASEAN, DEMAND_DIR, REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_csv, write_json

SCRIPT = "scripts_project/s3_4_shipping_data.py"
TABLE = DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
PE_CONFIG = SRC_DIR / "pypsa_eur_v2025.07.0_config.default.yaml"
PE_SCRIPT = SRC_DIR / "pypsa_eur_v2025.07.0_prepare_sector_network.py"
OUT = ROOT / "research_inputs/shipping_v5"
OIL_EFF, MEOH_EFF = 0.40, 0.46


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dem = pd.read_csv(TABLE, keep_default_na=False); t_sha = sha256(TABLE)
    reg_df = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    shares = {k: float(reg_df.loc[f"share_shipping_{k}_share_2050", "value"]) for k in ["methanol", "hydrogen", "oil"]}
    conv = OIL_EFF / MEOH_EFF
    rows = []
    for c in ASEAN:
        for account in ["DomesticShippingFuel", "InternationalShippingBunker"]:
            r = dem[(dem.country == c) & (dem.account == account)]
            v = float(pd.to_numeric(r.value_2050_mwh, errors="coerce").fillna(0).sum()) if len(r) else 0.0
            rows.append(dict(country=c, account=account, oil_equivalent_mwh=v, methanol_mwh=v * shares["methanol"] * conv, hydrogen_mwh=v * shares["hydrogen"] * OIL_EFF, oil_mwh=v * shares["oil"],
                             status=";".join(sorted(set(r.status))) if len(r) else "no row", decision_ref="10,22 (bunkers)" if account.startswith("International") else "22,34"))
    write_csv(rows, OUT / "SHIPPING_DEMAND_2050.csv", list(rows[0].keys()))
    df = pd.DataFrame(rows)
    tot = df.groupby("account").oil_equivalent_mwh.sum()
    reg = Registry(SCRIPT)
    cfg_sha, pe_sha = sha256(PE_CONFIG), sha256(PE_SCRIPT)
    reg.add("shipping_demand_domestic_2050", "Domestic shipping fuel 2050, oil-equivalent, sum of the D1 table rows DomesticShippingFuel (ASSEMBLY_V1_DOMESTIC_CONSTANT_2019 x AEO8 transport multipliers)", float(tot["DomesticShippingFuel"]), "MWh_oil_eq/a", "B",
            "D1 DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "account DomesticShippingFuel", t_sha, decision_ref="22,34")
    reg.add("shipping_demand_international_2050", "International marine bunkers 2050, oil-equivalent, sum of the D1 table rows InternationalShippingBunker (constant 2019, decision 10); switch research.s2.demand.international_bunkers shared with aviation",
            float(tot["InternationalShippingBunker"]), "MWh_oil_eq/a", "B", "D1 DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "account InternationalShippingBunker", t_sha, decision_ref="10,22")
    reg.add("shipping_demand_total_2050", "Shipping oil-equivalent demand served in S3-4 = domestic + international (the S2 deferred ledger carries the same 651.19 TWh; the 670.2 TWh quoted in the S3 instruction is not reproduced from the current D1 table)",
            float(tot.sum()), "MWh_oil_eq/a", "B", "D1 table; S2/S3 build receipt demand_s2.deferred", "both accounts", t_sha, decision_ref="10,22,34")
    reg.add("shipping_methanol_conversion", "Methanol energy per MWh oil-equivalent = shipping_oil_efficiency 0.40 / shipping_methanol_efficiency 0.46 (PyPSA-Eur config lines 636/635; add_shipping lines 5195-5200)", conv, "MWh_MeOH/MWh_oil_eq", "B",
            "PyPSA-Eur v2025.07.0 config.default.yaml", "lines 635-636", cfg_sha, decision_ref="10")
    for k, v in shares.items():
        reg.add(f"shipping_share_{k}_2050_applied", f"2050 shipping fuel share for {k} applied in S3-4 (D1 registry share_shipping_{k}_share_2050, PyPSA-Eur config lines 611-634)", v, "fraction", "B", "D1 registry / PyPSA-Eur config", f"share_shipping_{k}_share_2050", cfg_sha, decision_ref="10")
    reg.add("shipping_methanol_co2_at_use", "Shipping methanol combustion books 1/MWh_MeOH_per_tCO2 = 0.2482 tCO2/MWh in the consuming country's atmosphere (PyPSA-Eur shipping methanol link, efficiency2); fuel-origin split in S3-5 (decision 64)", 0.2482, "tCO2/MWh_MeOH", "B",
            "PyPSA-Eur v2025.07.0 prepare_sector_network.py add_shipping", "lines 5218-5227", pe_sha, decision_ref="10,64")
    reg.add("shipping_node_allocation", "Shipping loads are placed on the nodes by the Assembly-V1 allocation arrays of the same account (DomesticShippingFuel / InternationalShippingBunker), falling back to the transport shares", "allocation_arrays", "method", "B",
            "s2_layers.add_demand_layer", "allocation_manifest.json accounts", t_sha, decision_ref="10", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "shipping.csv")
    write_json(dict(script=SCRIPT, sources=dict(table=t_sha, pe_config=cfg_sha, pe_script=pe_sha), shares=shares, conversion=conv, rows=rows, totals_mwh=tot.to_dict()), OUT / "SHIPPING_EVIDENCE.json")
    print((df.pivot(index="country", columns="account", values="methanol_mwh") / 1e6).round(3).to_string()); print("totals TWh oil-eq:", (tot / 1e6).round(3).to_dict(), "methanol TWh:", round(float(tot.sum()) * conv / 1e6, 3))


if __name__ == "__main__":
    main()
