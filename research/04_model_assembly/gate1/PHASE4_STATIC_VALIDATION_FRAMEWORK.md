# Static validation framework

Reusable implementation: scripts_project/phase4_static.py. Integrated regression entry point: scripts_project/run_gate1_checks.py --output results_project/gate1_checks. No optimization or data workflow is invoked. tests/research/test_phase4_static.py has adversarial synthetic tests.

| Gate | Implemented hook | Control / limitation |
| --- | --- | --- |
| A Git/config | identity(repo, expected_commit, files) | Independent SHA and config hashes required |
| B duplicate names | demand and annual_loads | Unique Load/carrier **identifiers**; multiple Loads sharing a carrier is valid |
| C NaN/inf | demand / annual_loads | Reject missing/nonfinite data, no fill-to-zero |
| D negative | demand(allow_negative=...) | Explicit sign exceptions only; accounting emission Loads are not physical demand |
| E country conservation | conserve | Exact country/carrier key sets and independent MWh controls |
| F source→node | allocation | Complete node-country map, then country controls; no unknown-to-zero |
| G weights | snapshot_weights | Positive finite aligned roles; expected-hours mapping is caller supplied |
| H carriers | inventory | Actual bus carrier inventory |
| I cross-border | inventory edges | All Link ports plus Lines/Transformers; missing endpoints INVALID_ENDPOINT; unknown country UNKNOWN |
| J shared pools | bus_scope / inventory | Explicit country map first; names/location give heuristic GLOBAL/REGIONAL hints; unknown stays unknown |
| K policy carbon | inventory policy_constraints | Detect actual constraints; scope validation PENDING without independent contract |
| L coupling | inventory coupling | Multi-carrier Links and available/extendable capacity, not solved dispatch evidence |

Default preflight leaves A/D/E/F/K PENDING where independent controls are absent. No PASS-to-Full-SC inference. CLI returns nonzero for detected FAIL. Missing future controls are visible, not bypassed. In particular repeated carriers are not duplicate identities, negative accounting loads need explicit roles, and snapshot energy uses generator physical weights rather than unweighted sums. No country prefixes are guessed for unknown buses.

PyPSA 0.30.3 does not accept country as a built-in Bus constructor attribute. The synthetic test explicitly assigns the project metadata column, matching actual table usage. The initial failing fixture and its corrected final test output are both retained. This changes the test fixture, not model inputs.
