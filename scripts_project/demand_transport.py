"""Road final-energy contract, rail embedded, and four distinct fuel accounts."""
from demand_accounting import COUNTRIES
from demand_sources import row,cached,electricity


def build(sources):
    result=[];cache={x['Country']:x for x in sources['energy_cache']['records']}
    for c in COUNTRIES:
        result.append(cached(row(c,2019,'Transport','RoadParentFinalEnergy','all_final_energy',
            Posting=False,Required=False,Representation='REFERENCE',Status='REFERENCE_ONLY',
            Notes='Independent cached final-energy control, not an extra fuel Load; EV share not accepted'),
            sources['energy_cache'],cache[c].get('total road'),c+'/total road'))
        # Zero road electricity is empty raw selection in existing Phase3 trace.
        r=cached(row(c,2019,'Transport','HistoricalRoadElectricity','electricity',
            DemandType='DIRECT_ELECTRICITY',ParentAccount='Astar',OwnerAccount='Astar',
            IncludedInAstar=True,Posting=False,Required=False,Representation='EMBEDDED',
            Notes='Historical EV membership/quantity pending; retain any such energy inside Astar; no transfer performed'),
            sources['energy_cache'],cache[c].get('road electricity'),c+'/road electricity')
        result.append(r)
        for fuel in ['oil','gas','biomass']:
            result.append(cached(row(c,2019,'Transport','RoadResidualFuel',fuel,
                Notes='Base-year carrier observation; future residual vector requires accepted energy share and fuel composition'),
                sources['energy_cache'],cache[c].get('road '+fuel),c+'/road '+fuel))
        result.append(electricity(row(c,2019,'Transport','RailElectricity','electricity',
            DemandType='EMBEDDED',ParentAccount='Astar',OwnerAccount='Astar',IncludedInAstar=True,
            Posting=False,Required=False,Representation='EMBEDDED',Notes='Rail electricity occurs only within Astar; no independent rail Load'),
            sources['electricity'],'Consumption by rail'))
        # The total-rail cache combines diesel/biodiesel/electricity. Do not
        # invent an all-oil rail Load by subtracting rounded electricity.
        result.append(cached(row(c,2019,'Transport','RailFinalEnergyReference','mixed',
            Posting=False,Required=False,Representation='REFERENCE',Notes='Reference total only; fuel decomposition pending; no independent rail Load'),
            sources['energy_cache'],cache[c].get('total rail'),c+'/total rail'))
        result.append(row(c,2019,'Transport','TransportEmbeddedFuelParent','unclassified_fuel',
            DemandType='UNCLASSIFIED',LogicalDestination='',Notes='Rail fuel retained in one unresolved transport fuel parent; no extra rail oil Load or fabricated residual'))
        for year in [2030,2040,2050]:
            result.append(row(c,year,'Transport','RailElectricity','electricity',DemandType='EMBEDDED',
                ParentAccount='Astar',OwnerAccount='Astar',IncludedInAstar=True,Posting=False,Required=False,Representation='EMBEDDED',
                Notes='Future rail stays in Astar once; decomposition pending'))
            result.append(row(c,year,'Transport','TransportEmbeddedFuelParent','unclassified_fuel',DemandType='UNCLASSIFIED',LogicalDestination='',
                Notes='Rail fuel remains within one pending transport fuel parent; no duplicate rail Load'))
            result.append(row(c,year,'Transport','RoadEVFinalElectricity','electricity',
                DemandType='DIRECT_ELECTRICITY',Notes='External final-energy share pending; future EV excluded from future direct Astar; no kWh/km proxy'))
            for fuel in ['oil','gas','biomass']:
                result.append(row(c,year,'Transport','RoadResidualFuel',fuel,Notes='PENDING_FUTURE_GROWTH_AND_EV_ENERGY_PATH; carrier vector retained'))
    names={'InternationalShippingBunkerFuel':'InternationalShippingBunker','InternationalAviationBunkerFuel':'InternationalAviationBunker'}
    for x in sources['bunker_review']['records']:
        account=names.get(x['account'],x['account']);international=account.startswith('International')
        sector='Bunker' if international else 'Transport'
        r=cached(row(x['country'],2019,sector,account,'oil',
            DemandType='BUNKER_FUEL' if international else 'DIRECT_FUEL',Group='bunker',
            Notes='FIXED fuel obligation; FT is later endogenous supply. Review status: '+x['status']),
            sources['energy_cache'],x['base_text'],x['country']+'/'+x['cached_column'])
        if x['omitted_account_related_raw_records']:
            r['Status']='BLOCKER';r['Notes']+='; omitted transaction/commodity exists: no automatic correction'
        r['SourceLocator']+='; bunker_review.json '+x['country']+'/'+x['account']
        result.append(r)
        for year in [2030,2040,2050]:
            result.append(row(x['country'],year,sector,account,'oil',
                DemandType='BUNKER_FUEL' if international else 'DIRECT_FUEL',Group='bunker',
                Notes='PENDING_FUTURE_GROWTH; upstream default projection not accepted'))
    return result
