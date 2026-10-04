# Gate4 — export/readback verification

**SYNTHETIC_TEST_ONLY success path: PASS.** It calls the same component merge, demand binding and static validator as the Research assembler, exports a small NetCDF and reads it back. It does not represent a Research scientific result.

The fixture carries a real2920-snapshot2013/3h series, explicit Load carrier/sector/account/country attributes, a time-dependent generator availability, a bounded Biodiesel resource, electrolysis, annual-supply and one-way-Store hook metadata, and a legitimate non-carbon system constraint. Input time series, ownership, annual integrals, static components and hooks survive export/readback.

Positive/negative tests cover: compatible blend mass splitting; frozen missing memo; vintage/unit/transaction mismatch; strict retirement boundary; unknown and planned assets; total versus additional resource limits; required approved pathways without forced SMR; carbon-policy rejection while retaining legal constraints; mismatched demand destination; diverted or extra biomass supply; lost hooks; wrong physical carbon coefficient/country; and the production100-node guard. No optimiser variables or solver calls are required.

Test counts in individual logs: {"ASSET_TESTS": 18, "CONTINUE_REGRESSION": 18, "ASSEMBLY_REGRESSION": 17, "TOPOLOGY_REGRESSION": 9}. Additional Gate3 validation and configuration receipts are in evidence/TEST_RECEIPTS.json. Completed unaffected Gate1/Gate2 experiments were not rerun.

**Actual development assets:** both were exported and read back;100 node ownership, finite materialised parameters and profiles, no Load/solved-output leakage, carrier ownership and persisted battery/resource hook metadata were inspected. See evidence/ACTUAL_DEVELOPMENT_ASSET_VALIDATION.json. These checks do not establish complete demand, accepted survivor stock or complete carbon attribution. The complete2050 Research NetCDF was not exported. An input-gate exit2 is recorded only as a correct block, never as successful production assembly.
