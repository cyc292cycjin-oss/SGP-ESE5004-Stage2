import json
R = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3/smoke_v2/M12_BENEFIT/BENEFIT.json"
b = json.load(open(R)); o = b["owen"]; pI, pD = o["allocation_integrated_eur"], o["allocation_disconnected_eur"]
print("main", b.get("main_form"), {k: round((pD[k] - pI[k]) / 1e9, 3) for k in pI})
