"""S4E-2 data (decision 95): registry fragment s4e_2 - unified CO2 storage cost basis (modifying the unit cost of decision 89), pair-specific sea
distances, Lao transit then shipping, Lao transit and LNG sensitivities registered (not run), coalition run rule reference.

    python scripts_project/s4e_2_data.py
"""
from __future__ import annotations

import pandas as pd
import yaml

from d1_common import REG_DIR, ROOT, Registry

SCRIPT = "scripts_project/s4e_2_data.py"
INSTRUCTION_SHA = "e5c184c12a91a89ac52e151661cf593a75139396436b95bb75ef0c1cfbb7e9db"
LOC = "work/p1_step4e_20261017/S4E_CLAUDE_CODE_INSTRUCTION.md"
SRC = "S4E instruction S4E-2 (user decisions 2026-10-17 13:11-13:12 SGT)"
PYPSA_EUR_CONFIG_SHA = "bfbe9160db09c3e960b97173bc755492b7638e0f4a5081ffaa1dddd4635da787"


def main():
    R = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    cfg = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
    seq = float(cfg["research"]["s2"]["co2"]["sequestration_cost_eur_per_t"])
    ship = float(R.at["co2_extra_asean_shipping_chain_4500km", "value"]) * float(R.at["conv_usd2004_to_eur2020", "value"])
    zep = float(R.at["co2_extra_asean_offshore_storage_eur2009", "value"]) * float(R.at["conv_eur2009_to_eur2020", "value"])
    price = ship + seq
    reg = Registry(SCRIPT)
    reg.add("co2_extra_asean_storage_cost_unified", f"Decision 95 a (modifies the unit cost of decision 89): extra-ASEAN CO2 storage = IEAGHG 2004 shipping chain at 4,500 km "
            f"({ship:.4f} EUR2020/t) + the unified geological storage cost {seq:.0f} EUR/t (PyPSA-Eur v2025.07.0 sector.co2_sequestration_cost, the value of the national "
            "stores, research.s2.co2.sequestration_cost_eur_per_t). Reason: the same geological storage must not carry a different cost basis by location, otherwise storage is "
            "systematically pushed out of ASEAN (working principle 8; S4D: 30 vs 16.05 made intra-ASEAN shipping dominated). The +-50 % sensitivity now applies to this value",
            price, "EUR2020/tCO2", "C", "IEAGHG (2004) PH4/30 Table 5-3; PyPSA-Eur v2025.07.0 config.default.yaml sector.co2_sequestration_cost", "Table 5-3; config co2_sequestration_cost",
            PYPSA_EUR_CONFIG_SHA, sensitivity_low=0.5 * price, sensitivity_high=1.5 * price, decision_ref="95,89")
    reg.add("co2_storage_cost_zep_sensitivity", f"Decision 95 a sensitivity: ZEP 2011 offshore saline aquifer Medium (14 EUR2009 x conv) = {zep:.4f} EUR2020/t for every geological "
            f"storage (national stores, intra-ASEAN receivers, extra-ASEAN = {ship:.2f} + {zep:.2f} = {ship + zep:.2f}); override s2.co2.sequestration_cost_eur_per_t={zep:.4f}",
            zep, "EUR2020/tCO2", "C", "ZEP (2011) The Costs of CO2 Capture, Transport and Storage, Figure 19", "registry co2_extra_asean_offshore_storage_eur2009",
            R.at["co2_extra_asean_offshore_storage_eur2009", "source_sha256"], decision_ref="95,89", status="REFERENCE_ONLY")
    reg.add("s4e2_ship_distance", "Decision 95 b: intra-ASEAN shipping distance - research.co2.ship_distance = sea_path (main: pair-specific shortest sea path of CO2_SHIP_ROUTES_S4D2.csv) | "
            "route_factor (great-circle x co2_ship_route_factor 1.091, comparison switch)", "sea_path|route_factor", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="95,92",
            status="REFERENCE_ONLY")
    reg.add("s4e2_lao_transit_shipping", "Decision 95 c: after the rail transit to the nearest coast, Lao CO2 can be shipped along the shipping routes of the coastal node of that coast "
            "point into the national stores of other ASEAN countries; cost = land leg + ship leg + receiver storage (store unit cost); links '<node> co2 transit ship to <j>' (carrier "
            "'CO2 transit ship', maritime trade, both scenarios); research.co2.lao_transit_shipping on | off", "on|off", "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="95,93,92",
            status="REFERENCE_ONLY")
    reg.add("s4e2_sensitivity_lao_transit", "Decision 95 d (registered, not run): Lao transit to the nearest existing sea port of the author WPI subset "
            "(research.co2.lao_transit_destination=existing_port) and by truck (research.co2.lao_transit_mode=truck); both scenarios", "existing_port|truck", "flag", "B", SRC, LOC,
            INSTRUCTION_SHA, decision_ref="95,93", status="REFERENCE_ONLY")
    reg.add("s4e2_sensitivity_lng_uncapped", "Decision 95 e (registered, not run): LNG terminal expansion without cap, priced at 7,018 EUR/MW/a (research.s3.gas.lng_expansion="
            "uncapped_cost; all terminal nodes incl. proposed-only sites; the liquid-H2 cap keeps the rule cap; gate B14 has no cap in this mode)", "uncapped_cost", "flag", "B", SRC, LOC,
            INSTRUCTION_SHA, decision_ref="95,17,72", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4e_2.csv")
    print(dict(ship=ship, seq=seq, price=price, zep=zep, zep_total=ship + zep))


if __name__ == "__main__":
    main()
