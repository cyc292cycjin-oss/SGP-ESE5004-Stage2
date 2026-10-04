# Research build configuration — Gate4 resume

`configs/research/baseline.yaml` records AEO8 BAS as the regional final-demand anchor; the Road EV embedded override; constant2019 international bunker boundary; independent quantity-unconstrained fossil markets; local biomass obligation cap; no geological storage; post-build carbon validation.

`network_export_enabled=false`, `runnable_workflow=false`, `solver_allowed=false`, `scenario_switching=false` remain. This is a truthful blocked configuration, not a runnable Full-SC workflow. `legacy_final_adjustment=forbidden`, legacy demand builders forbidden, `only_elec_network=false`. The topology metadata now cites the already completed d13d5976 repair. Baseline carbon enable=false and its existing budgets are preserved.

The input preflight runs first. G4-CARBON-01 requires actual components after a permitted build; it does not block this numerical input check. No synthetic network is substituted for the requested complete2050 Research network.
