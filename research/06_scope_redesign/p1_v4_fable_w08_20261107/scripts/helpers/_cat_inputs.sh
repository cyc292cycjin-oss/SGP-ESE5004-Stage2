cd /home/jin/wt_v4_fable/research_inputs || exit 1
for f in industry_v4/CAPTIVE_COAL_2019.csv industry_v4/CEMENT_USGS_2019.csv industry_v4/HVC_PLANTS_V4.csv industry_v4/METHANOL_PLANTS_V4.csv industry_v4/MY_AMMONIA_FUEL_DUPLICATE.csv demand_v5/NCV_EXCEPTIONS.csv industry_v4/FUELWOOD_OUTSIDE_BALANCE.csv industry_v4/RESIDUE_CLASSES.csv industry_v4/NATIONAL_BALANCE_BIOMASS_COVERAGE.csv industry_v4/RESIDUE_RECORDS_2019.csv industry_v4/HOUSEHOLD_GASOLINE_2019.csv industry_v4/PRODUCT_DERIVED_INPUTS_V4.csv industry_v4/VN_HYBRID_ELECTRICITY_ROWS.csv gas_v5/W12_UNSD_GAS_2019.csv gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv gas_v5/FUGITIVE_FACTORS_V4.csv gas_v5/GAS_PRODUCTION_CAPS_2050.csv demand_v5/DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv industry_v4/out_ras/DEMAND_ANCHOR_C3_DEVIATION.csv industry_v4/out_iid/DEMAND_ANCHOR_C3_DEVIATION.csv industry_v4/out_ras/INDUSTRY_OUTPUT_2050_M08B.csv assembly_v1/sources/SDMX_DICTIONARY_EXTENSION.json biomass_v5/W12_UNSD_BAGASSE_2019.csv biomass_v5/W12_BAGASSE_SUPPLY_OVERESTIMATE.csv industry_v4/PRODUCT_ITEMS_V4.csv; do
  echo "##### $f"; cat "$f"; echo
done
echo "##### out_ras/V4_SWITCHES.json (head)"; head -60 industry_v4/out_ras/V4_SWITCHES.json
echo "##### out_ras INDUSTRY_2050_SUMMARY_V4.csv columns"; head -1 industry_v4/out_ras/INDUSTRY_2050_SUMMARY_V4.csv | tr ',' '\n' | head -80
echo "##### BIOMASS_POTENTIAL_ADJ_V4 totals"; grep -E "TOTAL" biomass_v5/BIOMASS_POTENTIAL_ADJ_V4.csv
echo "##### DEMAND_ANCHOR_AEO8_ATS.csv out_ras"; cat industry_v4/out_ras/DEMAND_ANCHOR_AEO8_ATS.csv | cut -d, -f1-12
echo "##### v3.1 DEMAND_ANCHOR_AEO8_ATS.csv"; cat demand_v5/DEMAND_ANCHOR_AEO8_ATS.csv | cut -d, -f1-12
