import json
r=json.load(open('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/phase1/V2_NETWORK_FACTS.json'))
for k in ("snapshots","components","bus_carriers","oil_pool_links","imports","maritime_trade","bev","nodes_by_country","nodes_ac_by_country","hooks"):
    print(k, json.dumps(r[k],ensure_ascii=False)[:1400])
print("diurnal"); 
for c,v in r["diurnal"].items(): print(c,v)
x=r["cross_border"]; print(json.dumps({k:x[k] for k in ("by_carrier","stock","fom_eur","rows_reversed")})[:1800])
print({k:round(v,2) for k,v in r["load_carriers_twh"].items()})
print(r["link_carriers"])
print(r["store_carriers"])
