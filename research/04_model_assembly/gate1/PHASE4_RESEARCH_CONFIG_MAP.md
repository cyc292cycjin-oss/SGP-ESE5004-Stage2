# Research configuration layer

Verified upstream order in Snakefile: config.default → plotting.default → solving.default → bundle_config → powerplantmatching_config → config.yaml; Snakemake merges before `migrate_config`. The research worktree has no tracked config.yaml. We did not run Snakefile's `copy_default_files()` or create an uncontrolled config.yaml.

`configs/research/composition.json` declares the same default layers followed by the frozen ASEAN config (with the approved carbon key fix), then a minimal research override. `scripts_project.phase4_static.config` uses upstream `_deep_merge_dicts` and `migrate_config` for a read-only composition. This is a declared foundation composition, not a claim that the current workflow consumes it automatically. A later gate must explicitly wire a reviewed effective config into the workflow.

| Identity | Override | Gate1 meaning |
| --- | --- | --- |
| baseline | configs/research/baseline.yaml | Empty map; foundation identity |
| integrated | baseline + integrated.yaml | Empty map; future placeholder |
| disconnected | baseline + disconnected.yaml | Empty map; future placeholder |
| validation | baseline + validation.yaml | Empty map; no reduced resolution yet |

All four effective configurations are asserted equal. `runnable_workflow=false`. No scientific scenario difference is implemented. Existing upstream defaults can still encode behavior incompatible with the Phase3 design; their inheritance here is not boundary acceptance.

Frozen design records for later implementation: A* is end-user final electricity parent; AEO8 generation is paper comparator and AEO8 final electricity a benchmark. Buildings/Transport use minimum-defensible accounts. Industry uses fixed final-energy core plus qualified substitution. Agriculture is fixed/embedded. Electricity is the future cross-border intervention; H2, physical gas expansion, CO2 cross-border are OFF; NH3/methanol network OFF/deferred. Power policy carbon and full-system reporting must be separate. All are DESIGN ONLY in Gate1. Source contracts are indexed and hashed in the input registry, backed by archive `f7710800b495b60767ab6b7a5963f38b41aa03b4`.

Audit JSON uses strings `inf`, `-inf`, `nan` only for non-finite optional configuration/metadata representation. It is not a runnable replacement for YAML. CSV registries are identities, not parameter overrides.
