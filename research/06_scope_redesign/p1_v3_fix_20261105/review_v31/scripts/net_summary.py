import json, sys
d = json.load(open(sys.argv[1]))
for lab, R in d.items():
    print("=====", lab, "snapshots", R["snapshots"], "w_min", R["weights_min"]["objective"], "w_sum", R["weights_sum"]["objective"])
    b = R["bunker"]
    print(" bunker: ports %d links %d non_link %s cols %s eff %s..%s tv_eff %d pmin %s..%s tv_pmin %d pmax_min %s ext %d/%d capcost %s..%s margcost %s..%s store e0=%s cyc=%s loss=%s e_min_pu=%s capcost=%s finals %d twins_ok %d" % (
        b["ports"], b["distinct_links"], b["non_link_attached"], b["port_cols"], b["eff_static_min"], b["eff_static_max"], b["eff_tv_present"], b["p_min_pu_static_min"], b["p_min_pu_static_max"], b["p_min_pu_tv_links"], b["p_max_pu_static_min"], b["extendable"], b["ports"], b["capital_cost_min"], b["capital_cost_max"], b["marginal_cost_min"], b["marginal_cost_max"], b["store"]["e_initial"], b["store"]["e_cyclic"], b["store"]["standing_loss"], b["store"]["e_min_pu"], b["store"]["capital_cost"], b["final_buses"], b["final_buses_with_usable_nonfossil_feeder"]))
    for c, D in sorted(R["countries"].items()):
        cb = D["captured_buses"]
        nb = len(cb)
        with_seq = sum(1 for s in cb.values() if s["sequestration_stores"])
        with_use = sum(1 for s in cb.values() if s["usable_use_links"])
        with_tr = sum(1 for s in cb.values() if s["n_transport"] > 0)
        with_buf = sum(1 for s in cb.values() if s["buffer_stores"])
        none_ = [bus for bus, s in cb.items() if not s["sequestration_stores"] and not s["usable_use_links"] and s["n_transport"] == 0]
        uses = sorted(set(u for s in cb.values() for u in s["usable_use_links"]))
        trk = sorted(set(t[1] for s in cb.values() for t in s["usable_transport"]))
        kinds = {k: v for k, v in D["removal_kinds"].items()}
        print(f" {c}: removal {D['removal_ports']} usable {D['usable_removal_ports']} | captured buses {nb}: seq {with_seq} use {with_use} transport {with_tr} buffer {with_buf} | no outlet: {none_[:3]} | uses {uses} | transport kinds {trk}")
        print(f"     kinds {kinds}")
    print(" tiny:", json.dumps(R["tiny_magnitudes"]))
    print(" tiny loads M02:", R.get("tiny_loads_window_M02"))
    print(" tiny loads year:", R.get("tiny_loads_full_year"))
    print(" shedding:", R["load_shedding_like_generators"])
