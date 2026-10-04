# Topology preflight

**TOPOLOGY_FIX_REQUIRED=YES.** Direct read of frozen `data/osm-plus-prebuilt/0.1.1/all_buses_build_network.csv` and `all_transformers_build_network.csv` confirms bus765 exists, bus766 does not, and TH transformer `transf_524_0` still connects 765→766 (115/230 kV). Exactly 1 transformer has an endpoint missing from this bus table. File hashes are in the input registry; full row is in evidence/TOPOLOGY.json.

This violates the endpoint contract and blocks acceptance of a later network assembled from these tables. It does not prevent pure demand-accounting development. A historically successful tutorial does not prove this frozen source is repaired: that is another source/config identity.

No repair guessed or applied. The known topology candidate branch has no approved source fix. A later review must determine the authoritative paired bus/transformer representation (restore valid bus or remove/replace a genuinely invalid reference only with evidence), then test connectivity/domestic grid consequences. Gate1 does not decide which physical asset to change.
