"""Separate R/S identities; no synthetic heat, cooking or district-heat stock."""
from demand_accounting import COUNTRIES
from demand_sources import row,cached,electricity


def build(sources):
    result=[];cache={x['Country']:x for x in sources['energy_cache']['records']}
    for c in COUNTRIES:
        for name,label in [('Residential','Consumption by households'),('Services','Consumption by commercial and public services')]:
            r=electricity(row(c,2019,'Buildings',name+'DirectElectricity','electricity',
                DemandType='DIRECT_ELECTRICITY',ParentAccount='Astar',OwnerAccount='Astar',
                Representation='EMBEDDED',IncludedInAstar=True,Posting=False,Required=False),sources['electricity'],label)
            r['Notes']='Separate R/S identity retained in Astar; no second electricity Load; numeric decomposition is unaccepted'
            result.append(r)
            for use in ['SpaceHeat','WaterHeat','Cooling','Cooking']:
                r=row(c,2019,'Buildings',name+use,'mixed' if use!='Cooling' else 'electricity',
                    DemandType='EMBEDDED',Representation='EMBEDDED',ParentAccount=name+'DirectEnergy',
                    OwnerAccount='Astar_and_original_fuels',Posting=False,Required=False,Status='EMBEDDED',
                    IncludedInAstar=(use=='Cooling'),HumanAcceptance='REPRESENTATION_ACCEPTED_VALUES_NOT_DEFINED',
                    Notes='No additional service obligation. Existing final electricity/fuel keeps ownership. Cooking is not space/water heat.')
                result.append(r)
            for fuel in ['oil','gas','biomass','coal']:
                r=row(c,2019,'Buildings',name+'Fuel',fuel,
                      Notes='Fixed final fuel; no useful-heat inference; cooking remains within original fuel. Coal not recast as electricity.')
                r=cached(r,sources['energy_cache'],cache[c].get(name.lower()+' '+fuel),c+'/'+name.lower()+' '+fuel)
                if fuel=='coal':r['Notes']+='; cache has no original R/S coal column; source recovery required'
                result.append(r)
        for year in [2030,2040,2050]:
            for name in ['Residential','Services']:
                result.append(row(c,year,'Buildings',name+'DirectElectricity','electricity',
                    DemandType='DIRECT_ELECTRICITY',Representation='EMBEDDED',ParentAccount='Astar',
                    OwnerAccount='Astar',Posting=False,Required=False,IncludedInAstar=True,
                    Notes='PENDING_FUTURE_GROWTH; separate R/S decomposition remains optional inside Astar'))
                for fuel in ['oil','gas','biomass','coal']:
                    result.append(row(c,year,'Buildings',name+'Fuel',fuel,Notes='PENDING_FUTURE_GROWTH; no default growth or heat conversion'))
    return result
