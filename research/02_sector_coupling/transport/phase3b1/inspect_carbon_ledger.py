"""Read only the saved tutorial pre-strip carrier and atmosphere connections."""
from pathlib import Path
import json
import xarray as xr
R=Path(__file__).resolve().parent
records=json.loads((R/'evidence/NETWORK_TRANSPORT_EVIDENCE.json').read_text())
entry=next(x for x in records if x['role']=='TUTORIAL_PRE_STRIP')
with xr.open_dataset(entry['path']) as ds:
    factors={str(n):float(ds.carriers_co2_emissions.sel(carriers_i=n)) for n in ds.carriers_i.values if str(n) in ['oil','gas','co2','H2']}
    loads=[]
    for i,n in enumerate(ds.loads_i.values):
        if ds.loads_bus.values[i]=='co2 atmosphere':
            loads.append(dict(name=str(n),carrier=str(ds.loads_carrier.values[i]),p_set=float(ds.loads_p_set.values[i])))
    oil_gen=[str(n) for n,c in zip(ds.generators_i.values,ds.generators_carrier.values) if c=='oil']
    rail_links=[str(n) for n,c in zip(ds.links_i.values,ds.links_carrier.values) if 'rail' in str(n).lower() or 'rail' in str(c).lower()]
out=dict(network_path=entry['path'],network_sha256=entry['sha256'],carrier_co2_emissions=factors,atmosphere_loads=loads,oil_supply_generators=len(oil_gen),rail_named_links=rail_links,global_constraints=entry['global_constraints'],method='read-only xarray static variables; no solver',interpretation='Rail oil direct Load has no combustion component; oil carrier is zero-factor in this sample. No active tutorial CO2Limit implied.')
(R/'evidence/CARBON_LEDGER_OBSERVATION.json').write_text(json.dumps(out,indent=2,allow_nan=False))
print(json.dumps(out,indent=2))
