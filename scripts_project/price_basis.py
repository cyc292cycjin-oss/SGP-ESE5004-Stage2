"""Research-side EUR2020 layer; retain frozen source values and prior rebasing.

No web refresh, no forecasts, no solver. Technology-data currency_year can be
source metadata AFTER values were rebased. Never use that field alone.
"""
from pathlib import Path
import argparse, copy, hashlib, json, math
import pandas as pd
import numpy as np

METHOD='ASSEMBLY_V1_COMMON_PRICE_YEAR_EUR2020'
DECISION='GATE4-20261006-FIXED-ACCOUNTS-EUR2020#B'
SERIES='MNA.A.N.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.IX.D.N'
PRIOR_REBASED={'investment','VOM','fuel'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read_index(path):
    d=pd.read_csv(path)
    for col,value in {'KEY':SERIES,'FREQ':'A','REF_AREA':'I9','STO':'B1GQ','UNIT_MEASURE':'IX','PRICES':'D','TRANSFORMATION':'N','UNIT_MULT':0}.items():
        if not d[col].eq(value).all(): raise ValueError('Wrong price index definition '+col)
    if d.TIME_PERIOD.duplicated().any() or not np.isfinite(d.OBS_VALUE).all() or not d.OBS_VALUE.gt(0).all():
        raise ValueError('Invalid annual index observations')
    if not d.COMMENT_TS.str.contains('Euro area 20 (fixed composition)',regex=False).all():raise ValueError('Wrong geographical composition')
    values=dict(zip(d.TIME_PERIOD.astype(int),d.OBS_VALUE.astype(float)))
    if 2020 not in values: raise ValueError('Missing base-year observation')
    return values

def rebase(value,current_price_year,index,already_model_year=None):
    if already_model_year is not None:
        if already_model_year!=2020:raise ValueError('Unknown prior normalisation')
        return float(value),1.
    if current_price_year is None or not math.isfinite(float(current_price_year)) or float(current_price_year)!=int(current_price_year):
        raise ValueError('Unknown actual price year; publication year cannot substitute')
    year=int(current_price_year)
    if year not in index:raise ValueError('Missing official observation '+str(year))
    factor=index[2020]/index[year]
    return float(value)*factor,factor

def same_source(a,b):
    return np.isclose(float(a['value']),float(b['value']),rtol=1e-12,atol=1e-10) and a['unit']==b['unit'] and a['source']==b['source']

def row_basis(row,pre):
    """Resolve the last real-price conversion, not the retained source year."""
    key=(row['technology'],row['parameter'])
    if key in pre.index and same_source(row,pre.loc[key]):
        if row['parameter'] in PRIOR_REBASED:
            return 2020,'TECHNOLOGY_DATA_V0_13_2_ALREADY_REBASED_EUR2020'
        return row['currency_year'],'NOT_IN_UPSTREAM_INFLATION_PARAMETER_FILTER'
    if str(row['source']).startswith('8th ASEAN Energy Outlook') and row['currency_year']==2020 and str(row['unit']).startswith('EUR'):
        return 2020,'AEO8_APPEND_USD2020_TO_EUR2020_WITH_FROZEN_TECHNOLOGY_DECLINE'
    raise ValueError('No compatible prior transformation evidence')

def build_layer(costdir,technology_data,index_file,output):
    index=read_index(index_file);rows=[];tables={};inputs={str(index_file):sha(index_file)}
    for p in [technology_data/'config.yaml',technology_data/'scripts/compile_cost_assumptions.py',technology_data/'scripts/_helpers.py']:
        inputs[str(p)]=sha(p)
    # The archived end-of-pipeline inflation stage affects these three parameters.
    cfg=(technology_data/'config.yaml').read_text()
    helper=(technology_data/'scripts/_helpers.py').read_text()
    compiler=(technology_data/'scripts/compile_cost_assumptions.py').read_text()
    if 'eur_year: 2020' not in cfg or 'paras = ["investment", "VOM", "fuel"]' not in helper or compiler.rfind('adjust_for_inflation(')>compiler.rfind('costs_tot.to_csv('):
        raise ValueError('Frozen prior inflation evidence differs')
    for year,suffix in [(2030,'elec'),(2050,'sec')]:
        rawpath=costdir/f'costs_{year}.csv';processed=costdir/f'costs_{year}_{suffix}.csv';prepath=technology_data/f'outputs/costs_{year}.csv'
        for p in [rawpath,processed,prepath]:inputs[str(p)]=sha(p)
        raw=pd.read_csv(rawpath);pre=pd.read_csv(prepath).set_index(['technology','parameter']);original=pd.read_csv(processed,index_col=0);model=original.copy()
        if raw.duplicated(['technology','parameter']).any() or pre.index.duplicated().any():raise ValueError('Ambiguous cost row identity')
        resolved={}
        for _,r in raw.iterrows():
            unit=str(r.unit);monetary=unit.startswith(('EUR','USD','GBP','DKK'))
            if not monetary and r.parameter!='FOM':continue
            t,p=r.technology,r.parameter;source_t={'hydrogen storage tank type 1':'hydrogen storage tank'}.get(t,t) if year==2030 else t
            scale=1000. if '/kW' in unit else 1.
            rec=dict(RowID=f'{year}:{t}:{p}',Technology=t,Parameter=p,TechnologyYear=year,SourcePublicationYear=None,SourceCurrency=unit[:3] if monetary else None,SourceCurrencyYear=r.currency_year,OriginalValue=float(r.value),OriginalUnit=unit,PreparedValue=None,UnitScale=scale,EffectivePriceYearBefore=None,PriorTransformation=None,Index2020=index[2020],IndexSourceYear=None,RebaseFactor=None,ModelValue=None,ModelCurrencyYear=None,Status='PENDING',Source=r.source,RawFile=str(rawpath),RawSHA256=inputs[str(rawpath)],PreCostSHA256=inputs[str(prepath)],PreparedSHA256=inputs[str(processed)],DecisionReference=DECISION)
            try:
                if not monetary:
                    rec.update(Status='NONMONETARY_PERCENT_UNCHANGED',ModelValue=float(r.value),PriorTransformation='FOM percent not rebased; monetary FOM derived from common-price investment')
                else:
                    current,basis=row_basis(r,pre);rec.update(EffectivePriceYearBefore=int(current),PriorTransformation=basis)
                    if not unit.startswith('EUR'):raise ValueError('Non-EUR requires explicit frozen FX reconciliation before real-price adjustment')
                    expected=float(r.value)*scale
                    if source_t not in model.index or p not in model or not np.isclose(expected,float(original.at[source_t,p]),rtol=1e-11,atol=1e-8):raise ValueError('Prepared value differs: override/aggregation must be resolved separately')
                    # Preserve the prepared numeric representation exactly when
                    # already EUR2020; unit-scale multiplication is evidence only.
                    value,factor=rebase(float(original.at[source_t,p]),current,index)
                    rec.update(PreparedValue=float(original.at[source_t,p]),ModelValue=value,ModelUnit=unit.replace('/kW','/MW'),RebaseFactor=factor,IndexSourceYear=index[int(current)],ModelCurrencyYear=2020,Status='ALREADY_EUR2020_UNCHANGED' if current==2020 else 'REBASED_TO_EUR2020')
                    model.at[source_t,p]=value;resolved[(source_t,p)]=rec
            except (ValueError,KeyError,TypeError) as exc:rec['PendingReason']=str(exc)
            rows.append(rec)
        # Annual cost combines one rebased investment base and an unchanged FOM%.
        # Defaults/overrides are preserved as source values, not assigned fake years.
        fixed='capital_cost' if suffix=='elec' else 'fixed'
        for t in model.index:
            if (t,'investment') in resolved:
                factor=resolved[(t,'investment')]['RebaseFactor']
                # Preserve original annualisation and component units exactly.
                model.at[t,fixed]=float(original.at[t,fixed])*factor
                monetary_fom=float(model.at[t,'investment'])*float(model.at[t,'FOM'])/100
                rows.append(dict(RowID=f'{year}:{t}:monetary_FOM',Technology=t,Parameter='monetary_FOM',TechnologyYear=year,ModelValue=monetary_fom,ModelCurrencyYear=2020,Status='DERIVED_ONCE_FROM_EUR2020_INVESTMENT_AND_UNCHANGED_FOM_PERCENT',Formula='investment_EUR2020 * FOM_percent /100',PreparedValue=float(original.at[t,'investment'])*float(original.at[t,'FOM'])/100,PriorTransformation=resolved[(t,'investment')]['PriorTransformation'],DecisionReference=DECISION))
        tables[str(year)]={'columns':list(model.columns),'index':list(model.index),'values':model.replace({np.nan:None}).values.tolist(),'original_sha256':sha(processed)}
    payload=dict(schema='research-cost-layer-v1',method=METHOD,decision=DECISION,model_price_year=2020,index_series=SERIES,index_file_sha256=sha(index_file),index_observations=index,source_inputs=inputs,rows=rows,tables=tables,solver_allowed=False)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    return payload

def load_table(path,year,source_path):
    layer=json.loads(Path(path).read_text());table=layer['tables'][str(year)]
    if table['original_sha256']!=sha(source_path) or layer['model_price_year']!=2020:raise ValueError('Cost layer source mismatch')
    return pd.DataFrame(table['values'],index=table['index'],columns=table['columns']),layer

def qualify_network_costs(n,layer,path):
    """Separate price usability from coverage/physical/policy qualification."""
    lookup={(r['TechnologyYear'],r['Technology'],r['Parameter']):r for r in layer['rows']}
    def status(year,t,p):
        r=lookup.get((year,t,p))
        if r and r.get('ModelCurrencyYear')==2020 and r['Status']!='PENDING':return 'EUR2020_SOURCE_TRACED'
        return 'SOURCE_PRICE_OR_TRANSFORMATION_PENDING'
    records=[]
    for typ in ['Generator','Link','Store','StorageUnit','Line']:
        for name,z in n.df(typ).iterrows():
            if z.get('cost_qualification')=='EXTERNAL_PENDING_FIXED_ACCOUNT':continue
            carrier=str(z.carrier);existing=z.get('asset_role')=='existing_survivor';year=2030 if existing else 2050
            tech={'solar':'solar-utility','solar rooftop':'solar-rooftop','onwind':'onwind','offwind-ac':'offwind','offwind-dc':'offwind','electricity distribution grid':'electricity distribution grid','battery charger':'battery inverter','battery discharger':'battery inverter','home battery charger':'home battery inverter','home battery discharger':'home battery inverter','battery':'battery storage','home battery':'home battery storage','H2 Electrolysis':'electrolysis','H2 electrolysis':'electrolysis','SMR':'SMR','SMR CC':'SMR CC','Fischer-Tropsch':'Fischer-Tropsch','FT':'Fischer-Tropsch','H2 Fuel Cell':'fuel cell','H2 fuel cell':'fuel cell','fuel cell':'fuel cell','H2':'hydrogen storage underground'}.get(carrier,carrier.removesuffix(' existing'))
            if typ=='Line':tech='HVAC overhead'
            if typ=='Store' and carrier=='H2':tech='hydrogen storage tank type 1 including compressor'
            if carrier in ['DC','B2B']:tech='HVDC overhead'
            rec=dict(ComponentType=typ,Component=name,Carrier=carrier,Technology=tech,TechnologyYear=year,CapitalPriceQualification='STRUCTURAL_ZERO_NO_NEW_CAPEX' if existing or z.capital_cost==0 else status(year,tech,'investment'),MarginalPriceQualification='FROZEN_ZERO_IMPLEMENTATION' if z.marginal_cost==0 else status(year,tech,'VOM')) if typ!='Line' else dict(ComponentType=typ,Component=name,Carrier=carrier,Technology=tech,TechnologyYear=year,CapitalPriceQualification=status(year,tech,'investment'),MarginalPriceQualification='NOT_APPLICABLE')
            if typ=='Generator' and carrier in ['gas','oil','coal','lignite']:rec['MarginalPriceQualification']=status(2050,carrier,'fuel')
            if typ=='Generator' and not existing and carrier in ['onwind','offwind-ac','offwind-dc','solar','solar rooftop'] and z.marginal_cost!=0:
                # Frozen config marginal_cost overrides raw VOM; no documented real
                # price year is inferred from its tiny numeric value.
                rec['MarginalPriceQualification']='CONFIG_OVERRIDE_PRICE_YEAR_PENDING'
            if existing:rec['FixedOMPriceQualification']=status(2030,tech,'investment')
            if typ=='Link' and tech=='Fischer-Tropsch':
                row=lookup.get((2050,tech,'VOM'),{})
                expected=float(row.get('ModelValue',float('nan')))*z.efficiency
                if not np.isclose(z.marginal_cost,expected):rec['MarginalPriceQualification']='KNOWN_VOM_NOT_ATTACHED_PENDING_ENGINEERING_BINDING'
            q='PENDING_BEFORE_SOLVE' if any('PENDING' in str(v) for v in rec.values()) else 'EUR2020_SOURCE_TRACED_OR_STRUCTURAL_ZERO'
            n.df(typ).loc[name,'price_qualification']=q;records.append(rec)
    n.meta.update(model_price_year=2020,price_layer_sha256=sha(path),price_method=METHOD,component_price_qualification=records)
    pending=[r for r in records if any('PENDING' in str(v) for v in r.values())]
    n.meta['qualification_dimensions']=dict(physical_integrity='VALIDATED_DEVELOPMENT_SCOPE',input_coverage='INCOMPLETE',price_usability='PENDING_BEFORE_SOLVE' if pending else 'ACTIVE_PRICED_PARAMETERS_EUR2020',full_cost_report=False,full_physical_emissions_report=False,policy_constraint_qualification='DISABLED_WITH_PENDING_ATTRIBUTION')
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['costdir','technology-data','index-file','output']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();build_layer(a.costdir,a.technology_data,a.index_file,a.output)
