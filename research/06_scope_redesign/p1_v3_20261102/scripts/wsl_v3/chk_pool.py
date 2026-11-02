import logging
import pandas as pd, pypsa
logging.disable(logging.WARNING)
B = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds"
v3 = pypsa.Network(f"{B}/integrated/integrated_2920_3h_unsolved.nc")
v2 = pypsa.Network("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/builds_v2/integrated/integrated_2920_3h_unsolved.nc")
for lab, n in (("v2", v2), ("v3", v3)):
    L = n.links; ob = n.buses.index[n.buses.carrier == "oil"]; nb = n.buses.index[n.buses.carrier == "oil non-fossil"]
    print(lab, "oil buses", len(ob), "non-fossil buses", len(nb), "oil pool links", int((L.carrier == "oil pool").sum()),
          "named oil pool", int(L.index.str.startswith("oil pool ").sum()), "named nf pool", int(L.index.str.startswith("oil non-fossil pool ").sum()))
    for node in ("MY_Peninsular22 0", "PH_Luzon9 0", "PH_Visayas10 0", "TH21 0"):
        print("  ", node, "oil bus", f"{node} oil" in n.buses.index, "nf bus", f"{node} oil non-fossil" in n.buses.index,
              "ofe bus", f"{node} oil final energy" in n.buses.index,
              "links", L[(L.bus0.astype(str).str.startswith(node + " oil")) | (L.bus1.astype(str).str.startswith(node + " oil"))].carrier.astype(str).value_counts().to_dict(),
              "loads", n.loads[n.loads.bus.astype(str).str.startswith(node + " oil")].sector.astype(str).tolist())
    # nodes with a fossil oil bus and no pool, or no non-fossil twin
    nodes = [b[:-4] for b in ob if b.endswith(" oil") and b not in ("ASEAN oil",) and b[:2] + " oil" != b]
    print("   oil-bus nodes without oil pool:", [x for x in nodes if f"oil pool {x}" not in L.index][:12])
    print("   oil-bus nodes without nf pool:", [x for x in nodes if f"oil non-fossil pool {x}" not in L.index][:12])
    ofe = L[L.carrier == "oil final-energy accounting"]
    fos = ofe[~ofe.index.str.endswith(" non-fossil")]
    print("   meters fossil", len(fos), "twins", len(ofe) - len(fos), "fossil meters without twin", [x for x in fos.index if f"{x} non-fossil" not in L.index][:12])
