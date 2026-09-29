# Added transmission-line country metadata repair

## Problem and evidence
On 2026-09-29 the tutorial failed in simplify_network with a country-consensus
assertion. Four existing lines were MY; Mambong – Bengkayang had a blank label.
The latter connects an MY bus0 to an ID bus1. In this upstream version,
base_network.py defines line.country from bus0 country, not as proof that the
line lies within one country. add_transmission_projects.py omitted this label.

## Change
Fill only blank/NaN line.country from bus0 after transmission projects have
been attached, before exporting the network. Fail if the bus country is absent.
Do not change bus0/bus1, capacities, impedances, voltages, lengths or project selection.

## Validation and limits
An in-memory check on the failed elec.nc found 23 missing labels. All could be
filled. Every other line column, the complete bus table and existing nonblank
country labels remained identical. The named interconnector remained MY–ID.
Source insertion and Python syntax were checked. This is not a successful
end-to-end workflow run or a demonstration of paper-result equivalence.

## Next run
Run simplify_network with the same three tutorial configuration files and
low-memory resource setting. Force add_transmission_projects once so dependent
networks are regenerated. Save the complete log and exit code, and record any
subsequent failure separately. Commit this repair separately after verification.
