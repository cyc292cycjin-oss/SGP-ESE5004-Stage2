"""Fixed final-energy core. Preserve coal/biomass; never substitute CO2 for MWh."""
import math
from demand_accounting import COUNTRIES,energy
from demand_sources import row,cached,electricity


def build(sources):
    result=[];cache={x['Country']:x for x in sources['energy_cache']['records']}
    industry={(x['country'],x['carrier']):x for x in sources['industry_cache']['records']}
    for c in COUNTRIES:
        r=electricity(row(c,2019,'Industry','IndustryDirectElectricity','electricity',
            DemandType='DIRECT_ELECTRICITY',ParentAccount='Astar',OwnerAccount='Astar',
            IncludedInAstar=True,Posting=False,Required=False,Representation='EMBEDDED',
            Notes='Industrial final electricity stays inside Astar; no second industry Load. No process/service conversion'),
            sources['electricity'],'Consumption by manufacturing, construction and non-fuel industry')
        if c=='TL':r['Notes']+='; TL explicit industry unavailable, retains unclassified electricity in valid parent'
        result.append(r)
        for fuel in ['electricity','gas','oil','coal','biomass','heat','hydrogen']:
            x=industry.get((c,fuel));raw=None
            if x:
                vals=[v for k,v in x.items() if k not in ('country','carrier')]
                if all(v not in ('',None) for v in vals):raw=format(math.fsum(energy(v) for v in vals),'.17g')
            r=row(c,2019,'Industry','IndustryFuel' if fuel!='electricity' else 'IndustryCacheElectricityReference',fuel,
                Notes='Base 2019 country/carrier sum of 13 cached industries; pre-NH3 deduction; raw calorific/feedstock boundary pending')
            if fuel=='electricity':r.update(Posting=False,Required=False,Representation='REFERENCE')
            if fuel in ('heat','hydrogen'):r.update(Posting=False,Required=False,Representation='PENDING',Notes='No accepted independent H2 or qualified heat service; no new service obligation')
            if c=='TL':r['Notes']+='; missing does not imply zero, unknown fuel parent remains unavailable'
            r=cached(r,sources['industry_cache'],raw,c+'/'+fuel+'; sum 13 columns',unit='MWh/year')
            if fuel=='coal' and r['ConvertedMWh'] is not None:
                r.update(EmissionsPresent=True,ExistingEnergyLoad=False,Notes=r['Notes']+'; MISSING_ENERGY_OBLIGATION in upstream add_industry')
            if fuel=='electricity' and raw is not None:r['Status']='REFERENCE_ONLY'
            result.append(r)
        for fuel in ['electricity','oil','biomass','coal']:
            r=row(c,2019,'Agriculture','AgricultureFinalEnergy',fuel,Notes='No agriculture technology model; retain each original fuel')
            if fuel=='electricity':
                r.update(DemandType='EMBEDDED',ParentAccount='Astar',OwnerAccount='Astar',
                         IncludedInAstar=True,Posting=False,Required=False,Representation='EMBEDDED')
                r=electricity(r,sources['electricity'],'Consumption in agriculture, forestry and fishing')
            else:r=cached(r,sources['energy_cache'],cache[c].get('agriculture '+fuel),c+'/agriculture '+fuel)
            if fuel in ('biomass','coal') and r['ConvertedMWh'] is not None:
                r['Notes']+='; candidate energy preserved; upstream add_agriculture does not consume this carrier'
            result.append(r)
        for year in [2030,2040,2050]:
            for sector in ['Industry','Agriculture']:
                result.append(row(c,year,sector,sector+'DirectElectricity','electricity',DemandType='EMBEDDED',
                    IncludedInAstar=True,ParentAccount='Astar',OwnerAccount='Astar',Posting=False,Required=False,Representation='EMBEDDED',
                    Notes='Future direct electricity remains within Astar; no separate Load; growth unaccepted'))
            for sector,fuels in [('Industry',['gas','oil','coal','biomass']),('Agriculture',['oil','biomass','coal'])]:
                for fuel in fuels:
                    result.append(row(c,year,sector,sector+'FinalEnergy',fuel,Notes='PENDING_FUTURE_GROWTH; no DEFAULT or zero-growth assumption'))
    return result
