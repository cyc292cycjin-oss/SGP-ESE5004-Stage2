# Gate2 derived demand layer

These six tables are typed observation/ownership contracts, **not accepted model
inputs**. `Posting=true` means the row is a proposed physical obligation owner;
it does not authorise a Load. `NumericAccepted=false` blocks materialisation.
No real country/year is presently allowed to materialise.

Run from this research repository with its existing Python environment:

```text
python scripts_project/build_research_demand.py --output results_project/gate2-rebuild --csv
python scripts_project/check_research_demand.py --output results_project/gate2-check.json
python tests/research/test_demand_accounting.py
```

The first command rebuilds all nine CSVs (six inputs, ledger, matrix, blockers).
It never overwrites the tracked inputs unless someone explicitly copies the
reviewed result. `--verify-originals` additionally checks original local files at
their recorded locations. The pinned `sources/` capsules permit deterministic
rebuild without those external files; their manifest and original SHA256 hashes
distinguish an observation copy from full independent source re-verification.

CSV uses UTF-8 BOM, quoted fields and CRLF. Blank annual values are unknown or
unquantified contracts; explicit zeros require `ZeroEvidence`. Status records
numeric provenance independently from representation acceptance. `RawValue=0`
with `ConvertedMWh` blank is a suspect cache zero, not a new zero demand.

No automatic fallback to AEO8 generation, DemandCast, `.97` losses, industrial
DEFAULT growth, default heat shares, stock or rail Loads is available in the
research demand entry point. Upstream sources are retained for provenance, and
the upstream Snakefile is not a runnable research entry point. The separate
composition recipe still sets `runnable_workflow=false`.

All source amounts retain their original observation/cache year. The industry
file named `base_industry_totals_2030.csv` is a **2019 base** country/carrier table
before ammonia deduction; its filename is not its statistical year.

Road electrification is an external share on final-energy MWh. It does not claim
equal useful traction service. Synthetic transfer/allocation tests are not
ASEAN demand estimates or accepted real temporal/spatial allocations.

The user accepts numeric source/year/boundary, then a later reviewed change can
record acceptance and create explicit transfers. Do not edit acceptance flags
by hand without a decision record. Carrier/carbon/topology/network assembly and
all solving remain outside Gate2.
