# Raw-to100-node mapping provenance

Status: **PARTIAL_SOURCE_CHAIN_RECOVERED_SECOND_LEG_CANDIDATE_ONLY**.

The frozen tutorial cache contains busmap_elec_s.csv (2,522 raw buses→1,202 simplified buses), busmap_elec_s_50.csv (1,202 rows), and elec_s.nc. The paper input reference contains100 geographic nodes, but its original100-node busmap is absent from the reviewed cache. Git5bacad702ccfed17ad19ab510fa710651e966f2c tracks only a custom-map template; no full100-node assignment has been recovered. This is a bounded evidence statement, not proof no original exists elsewhere.

`recover_asset_mapping.py` composes the first leg with a candidate second leg. It uses the50-node map only to identify the frozen country/region/original AC-partition prefix. It verifies the partition against topology of elec_s.nc, filters the existing100-node targets to exactly that prefix and country, and chooses minimum great-circle distance with a stable name tie-break. It never uses p_nom_opt/s_nom_opt, re-clusters the network or creates a new bus/line. It never falls back to national nearest distance.2,516 raw-bus candidates are returned,5 have no compatible target and1 no compatible simplified mapping; all remain PENDING.

The reference100-node topology and2013 profiles are unchanged. Profile assignment to historical assets needs its own qualified performance/profile contract: geometry compatibility does not establish original author membership or an observed plant weather curve. This proxy may change within-partition asset placement relative to the unavailable author map and requires human scientific acceptance. Country and partition checks also execute in the production stock integrator.

Legacy base/elec cache files expose the known dangling-transformer issue; they were only read and were not used to infer partitions. Partition checking uses the cached simplified network; the prior765/766 repair and current reference topology were not altered. Full source paths and SHA256 are in evidence/ASSET_MAPPING_CANDIDATE.json. The exact original100-node map, if later recovered, can replace the proxy after identity/partition validation.

The six unassigned raw buses are explicit:765 has a null first-leg mapping in the old cache;843/2100/2101/844/964 map to simplified844, whose source country is MY but cached cluster prefix is TH2. The candidate refuses this country-label conflict. This does not undo the approved765/766 topology repair or create a new line/bus.
