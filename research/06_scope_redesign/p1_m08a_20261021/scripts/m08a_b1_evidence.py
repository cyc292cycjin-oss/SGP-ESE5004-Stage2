"""M08a supplement 01 section 2 evidence (no solve): b1 (disconnected.co2_shipping_intra_asean = forbid) keeps a permanent CO2 sink for
every country - in particular the landlocked LA keeps only its transit corridor to extra-ASEAN storage.

Three checks on the S4M-3 disconnected base network (built with an earlier config; evidence of the topology, not production inputs):
  1. official path: m08a_variants.derive(forbid) with --allow-stale-base (national stores as built in S4M-3, D1 potentials);
  2. A5-adjusted: the same base with the national stores set to the unified ERIA-GCCSI 2024 P50 caps of M08a A5 IN MEMORY (stores of
     countries with cap 0 - TL - removed with every link into them; e_nom_max = potential / 50), then m08a_layers.apply_co2_shipping(forbid);
  3. derive(coalition.remove_countries [VN] + forbid): LA keeps its corridor when the transit state leaves the coalition.
Variant networks go to a scratch folder and are deleted; the JSON / CSV evidence is kept.

    PYTHONHASHSEED=0 python m08a_b1_evidence.py --repo /home/jin/wt_m08a_20261021 \
        --base /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m3/builds/disconnected/disconnected_2920_3h_unsolved.nc \
        --scratch /home/jin/m08a_scratch_b1 --out <work dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def a5_adjust(n, caps: dict) -> dict:
    """Unified A5 caps on the national stores, in memory: cap 0 -> store, its bus and every link into it removed."""
    st = n.stores[n.stores.carrier == "co2 sequestered"]
    out = {}
    for name, z in st.iterrows():
        c = str(z.country); cap = float(caps[c])
        if cap <= 0:
            into = list(n.links.index[n.links.bus1 == z.bus])
            n.mremove("Link", into); n.mremove("Store", [name]); n.mremove("Bus", [z.bus])
            out[c] = dict(action="removed (unified potential 0)", links_removed=len(into), cap_before_t=float(z.e_nom_max))
        else:
            out[c] = dict(action="cap set", cap_before_t=float(z.e_nom_max), cap_after_t=cap)
            n.stores.at[name, "e_nom_max"] = cap
    n.meta["research_co2_storage"] = dict(n.meta.get("research_co2_storage", {}), caps_t_per_year=caps)
    return out


def rows(led: dict, caps: dict, case: str) -> list:
    out = []
    for c in sorted(led["sink_channels_after"]):
        b, a = led["sink_channels_before"].get(c, {}), led["sink_channels_after"][c]
        out.append(dict(case=case, country=c, buffered_nodes=a["nodes"], process_emission_nodes=a["process_emission_nodes"],
                        national_cap_mt_per_year=round(a["national_cap_t_per_year"] / 1e6, 4), unified_cap_mt_per_year=round(float(caps.get(c, 0.0)) / 1e6, 4),
                        sinks_before="+".join(b.get("sink_kinds", [])), sinks_after="+".join(a["sink_kinds"]),
                        links_before=json.dumps(b.get("direct_links_by_carrier", {}), sort_keys=True), links_after=json.dumps(a["direct_links_by_carrier"], sort_keys=True),
                        nodes_without_sink_after=len(a["nodes_without_sink"]), feasible_outlet=bool(a["sink_kinds"]) and not a["nodes_without_sink"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--scratch", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import pandas as pd
    import pypsa
    from m08a_layers import apply_co2_shipping
    from m08a_variants import derive
    from phase4_static import config
    from s2_layers import co2_storage_caps
    cfg = config(a.repo, "disconnected")
    reg = pd.read_csv(a.repo / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    caps, pots, info = co2_storage_caps(cfg["research"]["s2"]["co2"], reg)
    ev = dict(schema="m08a-b1-sink-channels-v1", solver_runs=0, base=dict(path=str(a.base), sha256=sha(a.base)), unified_caps_t_per_year=caps,
              unified_table=info, note="base = S4M-3 disconnected build (earlier config): topology evidence; case a5_adjusted applies the A5 caps in memory", cases={})
    a.scratch.mkdir(parents=True, exist_ok=True)
    table = []
    # 1. official path (stale base allowed: evidence)
    r = derive(a.repo, a.base, a.scratch / "forbid", {"disconnected.co2_shipping_intra_asean": "forbid"}, None, True)
    led = r["ledgers"]["co2_shipping"]
    ev["cases"]["s4m3_as_built"] = dict(output_sha256=r["output"]["sha256"], components=r["output"]["components"], removed_by_carrier=led["removed_by_carrier"],
                                        landlocked_transit=led["landlocked_transit"], sink_channels_before=led["sink_channels_before"], sink_channels_after=led["sink_channels_after"])
    table += rows(led, caps, "s4m3_as_built")
    # 2. A5-adjusted national stores, then b1
    n = pypsa.Network(str(a.base))
    adj = a5_adjust(n, caps)
    led2 = apply_co2_shipping(n, "forbid")
    ev["cases"]["a5_adjusted"] = dict(a5_adjustment=adj, removed_by_carrier=led2["removed_by_carrier"], landlocked_transit=led2["landlocked_transit"],
                                      sink_channels_before=led2["sink_channels_before"], sink_channels_after=led2["sink_channels_after"])
    table += rows(led2, caps, "a5_adjusted")
    # 3. remove VN + b1
    r3 = derive(a.repo, a.base, a.scratch / "minusVN_forbid", {"coalition.remove_countries": ["VN"], "disconnected.co2_shipping_intra_asean": "forbid"}, None, True)
    led3 = r3["ledgers"]["co2_shipping"]
    ev["cases"]["minus_VN_forbid"] = dict(output_sha256=r3["output"]["sha256"], removed_by_carrier=led3["removed_by_carrier"], landlocked_transit=led3["landlocked_transit"],
                                          sink_channels_after=led3["sink_channels_after"], remaining_countries=r3["ledgers"]["coalition"].get("remaining_countries"))
    table += rows(led3, caps, "minus_VN_forbid")
    for p in a.scratch.rglob("*.nc"):
        p.unlink()
    ev["table"] = table
    d = a.out / "evidence"; d.mkdir(parents=True, exist_ok=True)
    (d / "M08A_B1_SINK_CHANNELS.json").write_text(json.dumps(ev, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    pd.DataFrame(table).to_csv(d / "M08A_B1_SINK_CHANNELS.csv", index=False)
    shutil.rmtree(a.scratch, ignore_errors=True)
    for t in table:
        print(t["case"], t["country"], t["sinks_before"], "->", t["sinks_after"], t["national_cap_mt_per_year"], t["feasible_outlet"])


if __name__ == "__main__":
    main()
