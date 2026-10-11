# Approved Scheme A controlled source version

Version: `EXACT_SOURCE_CLOSURE_A_MAX_ACCOUNT_V1_20261011`.
Rule: `EXACT_SOURCE_CLOSURE_A_MAX_ACCOUNT_V1`, explicitly approved by the user and ChatGPT.
Parent audit commit: `53c2b28632cb577136d48ebb843823967f0b1c25`.
Scientific source commit: `b9be7d0ab788a4151346c098d2e657c7e94a22da`.

This directory is a new **unbound source recipe and fixed-account export**, not a new assembled PyPSA network or LP. The old recipe, allocation, network, CSC, certificates, solver results and consumption marks are retained. It is never selected by the old assembly defaults automatically.

- `carrier_fragment.json`: complete existing unbound recipe, with only approved Store `e_nom`, `e_initial` and route `annual_cap_mwh` changes. Existing JSON `Infinity` capacity values retain the original Python-JSON representation.
- `external_pending_fixed_accounts.json`: matching 807-account export, with exactly 180 `QuantityMWh` changes. All prices and physical CO2 factors keep their previous NULL semantics.
- `LOADS_AND_WEIGHTS_REFERENCE.json`: immutable original allocation/NetCDF references and individual Load hashes, no regenerated time series. Preexisting all-zero allocation columns remain without a Load, as in `assembly_components.bind_loads`.
- `EXACT_SOURCE_CLOSURE_A_CHANGESET.json`: approved before/after double hex and exact deltas.
- `EXACT_SOURCE_CLOSURE_A_VERSION_MANIFEST.json`: parent and file bindings. The approval authorizes this source derivation and static acceptance only.

Future assembly must explicitly bind this recipe **together with this account export and the unchanged allocation**, create a new assembly manifest, and check resulting Q-related bounds under separately authorized work. The old Gate3/Gate4 manifest and accounting-qualification report are historical evidence, not current certificates for this new recipe. No old manifest is overwritten or presented as covering the new version.

The builder is `scripts_project/exact_source_closure_a.py`. The independent checker is `scripts_project/verify_exact_source_closure_a.py`; it reads the derived files from disk and checks against immutable source arrays and the frozen NetCDF. They do not import PyPSA or any optimizer. The builder refuses an existing output directory. Reproduction must use a separate empty destination; do not rerun over this version.

Scope: source-static closure only. D<=Q is guaranteed for the specified groups; D=Q and full-LP feasibility are not claimed. No scientific approval or solver authorization beyond Scheme A is implied. G6-05 remains PAUSED_BY_USER.
