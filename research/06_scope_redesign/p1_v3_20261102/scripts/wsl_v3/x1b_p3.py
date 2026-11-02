"""X1b patch 3: the static validation of the build compares the corridor table without the plant lines and checks those against their own ledger."""
W = "/home/jin/wt_v3_20261102/"
p = W + "scripts_project/s2_network.py"; s = open(p, encoding="utf-8", newline="").read()
a = '''        actual = {("Line", x) for x in n.lines.index[n.lines.border_class == "cross_border"]} | {("Link", x) for x in n.links.index[(n.links.border_class == "cross_border") & (n.links.transport_carrier == "electricity") & fwd]}
        if actual != expected_edges:
            raise ValueError("Cross-border electricity set differs from the corridor table")
'''
b = '''        plant = n.links.carrier == DEDICATED_CARRIER   # V3 X1b: the plant lines are not corridor stock; they follow their own table
        actual = {("Line", x) for x in n.lines.index[n.lines.border_class == "cross_border"]} | {("Link", x) for x in n.links.index[(n.links.border_class == "cross_border") & (n.links.transport_carrier == "electricity") & fwd & ~plant]}
        if actual != expected_edges:
            raise ValueError("Cross-border electricity set differs from the corridor table")
        if set(n.links.index[plant & fwd]) != {r["link"] for r in n.meta.get("research_dedicated_lines", {}).get("lines", [])}:
            raise ValueError("Plant lines differ from their ledger")
'''
assert s.count(a) == 1; s = s.replace(a, b)
a = "from v3_layers import add_dedicated_plant_lines, add_liquid_shipping, apply_ev_structure\n"
b = "from v3_layers import DEDICATED_CARRIER, add_dedicated_plant_lines, add_liquid_shipping, apply_ev_structure\n"
assert s.count(a) == 1; s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s); print("patched")
