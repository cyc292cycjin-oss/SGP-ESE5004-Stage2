# Direction-aware line country metadata

## Evidence
The prior blank-label repair succeeded (23 labels filled). The next failure
in simplify_network concerned lines 1274599202-1_0 and 1274599211-1_0.
Their respective bus0/bus1 pairs are 1098/2114 and 2114/1098; the endpoint
countries are VN/KH and KH/VN. Both original country labels follow bus0.
PyPSA 0.30.3 aggregatelines sorts the mapped endpoint IDs before grouping,
but retains the original direction-dependent country labels.

## Fix and scope
A project-local adapter recomputes only line.country using mapped, ordered
bus0 and the corresponding clustered bus country before delegating to the
original PyPSA function. Bus country consensus, all electrical strategies,
line groupings and bus mapping remain active. The input line table is restored
in a finally block. Both simplify_network and cluster_network use the adapter.
Before exporting, line.country is refreshed from bus0 again after the workflow
has restored national bus countries from temporary subregion classifications.
The installed PyPSA library is not edited; the earlier missing-label fix stays.

## Verified checks
- Original opposite-direction country assertion reproduced in a two-bus test.
- Adapter succeeds with identity and order-reversing cluster IDs.
- Input line table is restored unchanged.
- Every non-country aggregated line attribute matches original PyPSA on the
  same small network with the redundant country column omitted.
- The real conflicting VN/KH pair passes with the workflow's existing
  descriptive-field aggregation strategies.

These checks do not establish full workflow success or paper equivalence.
Next run only the concrete elec_s.nc target, retaining the low-memory settings.
Do not force add_transmission_projects again: its repaired output already exists.
Save the new log and exit code and commit this repair separately after review.
