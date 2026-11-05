import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("top keys:", list(d.keys()))
for net in d["networks"]:
    print("\n=====", net["label"], net["scenario"], "passed:", net.get("passed"), "zero_slack_forcing_rows:", net.get("zero_slack_forcing_rows"))
    for k in net:
        if k not in ("constraints", "required_constraint_hooks"):
            v = net[k]
            if isinstance(v, (dict, list)):
                s = json.dumps(v, ensure_ascii=False)
                print(" ", k, ":", s[:1500])
            else:
                print(" ", k, ":", v)
    for c in net["constraints"]:
        if c["name"].startswith("research_country_co2_limit") or c["name"].startswith("research_co2_storage_cap") or c["name"].startswith("research_bunker"):
            print("  -", c["name"], c.get("form"), "rows", c.get("rows"), "cap", c.get("cap_min"), "ports", c.get("ports"), "in", c.get("inflow_ports"), "rem", c.get("removal_ports"), "two", c.get("two_way_ports"), "zero", c.get("zero_ports"), "->", c.get("verdict"))
            if c.get("removal_examples"):
                print("      removal examples:", c["removal_examples"][:6])
    if net["label"] != "F1":
        break
