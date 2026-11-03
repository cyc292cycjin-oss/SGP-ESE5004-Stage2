import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
P = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER"]
for k, v in d["references"].items():
    i = v["integrated"]["owen_alpha_main_eur"]; r = v["disconnected"]["owen_alpha_main_eur"]
    print(k, f"B6 {v['b6_bn']:.4f}", " ".join(f"{p}:{(r.get(p, 0) - i.get(p, 0)) / 1e9:+.3f}" for p in P))
