# Gate4 Research build configuration

Target asset/technology year2050; operating weather/input-shape year2013;3h;8760h. The human asset boundary is ASSEMBLY_V1_2050_SINGLE_YEAR_SURVIVING_ASSETS, with strict retirement-year semantics. Source-aged existing capacity, resource occupancy and existing O&M are not silently inferred. Source-qualified electric status is still pending.

Input ownership/decision configuration remains configs/research/baseline.yaml. Carbon policy=false; no solver; no scenario intervention. The independent production DAG is workflow/research_assembly.smk; recorded source paths are in evidence/PRODUCTION_SOURCE_PATHS.json. Generated asset_bundle lives under results_project/assembly_v1/assets and currently has DEVELOPMENT_ASSETS_BUILT_FULLSC_NOT_COMPLETE status.

Existing131 allocations are reused; the two MY road accounts use the same accepted node/time method. The allocation manifest binds the current registry SHA; source metadata changes do not permit use of a stale registry manifest. Fixed fuel profiles and port/airport weights remain explicit proxies.
