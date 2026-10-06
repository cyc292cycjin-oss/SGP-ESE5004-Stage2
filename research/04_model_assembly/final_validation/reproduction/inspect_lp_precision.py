from pathlib import Path
from decimal import Decimal as D
import json,pypsa,numpy as np
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');E=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_final_validation/evidence')
n=pypsa.Network(R/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc')
bybus=n.loads_t.p_set.T.groupby(n.loads.bus).sum().T;groups={}
for r in n.meta['external_pending_fixed_accounts']:
 k=r['Meter'];link=n.links.loc[k];stock=n.stores.loc[r['FixedAccountID']]
 assert link.efficiency==1 and stock.standing_loss==0 and stock.e_min_pu==0 and not stock.e_cyclic
 g=groups.setdefault(link.bus1,{'resources':[],'original_stock':0.,'lp_stock':D(0)})
 g['resources'].append(r['FixedAccountID']);g['original_stock']+=stock.e_initial;g['lp_stock']+=D(format(stock.e_initial,'.12g'))
rows=[]
for bus,g in groups.items():
 total=sum(D(format(x,'.12g'))*D(24) for x in bybus[bus]);gap=total-g['lp_stock']
 rows.append(dict(bus=bus,resources=g['resources'],LPRequiredMWh=str(total),LPAvailableMWh=str(g['lp_stock']),LPExcessMWh=str(gap),OriginalFloatingDifferenceMWh=float(bybus[bus].sum()*24-g['original_stock']),DailyDemandMW=float(bybus[bus].iloc[0]),ConstantDemand=bybus[bus].nunique()==1))
rows.sort(key=lambda r:D(r['LPExcessMWh']),reverse=True)
(E/'LP_PRECISION_ENERGY_SCREEN.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows[:4],indent=2))
