"""Read-only per-event source/topology evidence; no policy assignments or model."""
import argparse,csv,hashlib,json,subprocess
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import numpy as np,pypsa,highspy
from gate5_resources import sha
from inventory_audit_3h import INPUT_SHA
from gate6_result import write
UPSTREAM='a3616a68ee44592af6527ca9024a90f1956646ae'

def run(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    source=root/'results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc'
    assert sha(source)==INPUT_SHA
    from pypsa.optimization.optimize import OptimizationAccessor
    with patch.object(OptimizationAccessor,'create_model',side_effect=AssertionError('NO MODEL')),patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')):
        n=pypsa.Network(source);pending=[r for r in n.meta['physical_carbon_map'] if r['policy_weight'] is None];assert len(pending)==200
        rows=[];detail=[]
        for r in pending:
            z=n.links.loc[r['component']];h2=z.bus1;node=h2.removesuffix(' :: H2')
            h2_inputs=n.links[n.links.bus1.eq(h2)];h2_outputs=n.links[n.links.bus0.eq(h2)]
            h2_stores=n.stores[n.stores.bus.eq(h2)]
            ft=h2_outputs[h2_outputs.carrier.eq('Fischer-Tropsch')]
            cells=h2_outputs[h2_outputs.carrier.eq('H2 Fuel Cell')]
            # All relevant ports of captured CO2 and downstream oil, not technology-name guessing.
            cap=r['captured_destination'];cap_members=[];oil_sinks=[];sectors=set();electric=[]
            if cap:
                for name,link in n.links.iterrows():
                    for port in ['bus0','bus1','bus2','bus3']:
                        if link[port]==cap:cap_members.append(dict(link=name,port=port,carrier=link.carrier,coefficient=-1. if port=='bus0' else float(link['efficiency' if port=='bus1' else 'efficiency'+port[-1]])))
            for name,f in ft.iterrows():
                oil=f.bus1
                for sink,s in n.links[n.links.bus0.eq(oil)].iterrows():
                    oil_sinks.append(sink)
                    if n.buses.at[s.bus1,'carrier'] in ['AC','DC']:electric.append(sink)
                    for _,load in n.loads[n.loads.bus.eq(s.bus1)].iterrows():sectors.add(str(load.sector))
            good=(r['PhysicalReportingQualified'] is True and np.isclose(z.efficiency2,r['coefficient']) and z.bus2=='ReportingCO2 atmosphere'
                and np.isclose(r['gas_input_carbon_factor'],r['coefficient']+r['captured_carbon_factor'])
                and len(ft)==1 and len(cells)==1 and len(h2_stores)==1)
            if cap:good=good and z.bus3==cap and np.isclose(z.efficiency3,r['captured_carbon_factor'])
            classification='SHARED_USE_METHOD_REQUIRES_DECISION' if good else 'MISSING_OR_CONTRADICTORY_EVIDENCE'
            row=dict(EventID=r['component'],Technology=r['carrier'],Country=r['country'],Node=node,
                Classification=classification,PhysicalFactClassification='SOURCE_SUPPORTED_MAPPING' if good else 'MISSING_OR_CONTRADICTORY_EVIDENCE',
                Family='F1_H2_SHARED_POOL'+(';F2_CAPTURE_RECYCLE_ATTRIBUTION' if cap else ''),
                PolicyWeight='null',PolicyAttributionQualified=False,PhysicalReportingQualified=r['PhysicalReportingQualified'],
                GasInput_tCO2_per_MWh=r['gas_input_carbon_factor'],ImmediateAtmosphere_tCO2_per_MWh=r['coefficient'],CapturedTransfer_tCO2_per_MWh=r['captured_carbon_factor'],
                H2Efficiency=float(z.efficiency),GasBus=z.bus0,H2Bus=h2,AtmosphereBus=z.bus2,CapturedBus=cap or '',
                H2Producers=';'.join(h2_inputs.index),H2Store=';'.join(h2_stores.index),H2Consumers=';'.join(h2_outputs.index),
                DirectH2Loads=int(n.loads.bus.eq(h2).sum()),FTDownstreamOilConsumers=';'.join(oil_sinks),FTDownstreamLoadSectors=';'.join(sorted(sectors)),FTDownstreamPowerConsumers=';'.join(electric),
                PermanentStorageAtCapturedBus=int(n.stores.bus.eq(cap).sum()) if cap else 0,
                PendingReason='Shared physical H2 pool has electricity and FT uses; no accepted source/use attribution method. '+('Captured transfer feeds FT; release destination must remain coupled to actual carbon and no second capture credit.' if cap else ''),
                FrozenInputSHA256=INPUT_SHA,SourceIdentity=r['source'],
                Evidence='Frozen NetCDF physical_carbon_map + Link bus0/1/2/3 and efficiencies + Store/Load incidence; upstream '+UPSTREAM+':prepare_sector_network.py:506-524,686-698,1408-1500,3601-3667; CARBON_SCOPE_FREEZE.md')
            rows.append(row);detail.append(dict(event=r['component'],physical_map=r,captured_bus_port_incidence=cap_members,h2_store_rules=[dict(name=k,e_cyclic=bool(v.e_cyclic),standing_loss=float(v.standing_loss),e_initial=float(v.e_initial)) for k,v in h2_stores.iterrows()]))
        with (out/'DEC_ATTRIBUTION_ITEMS.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        write(out/'DEC_PHYSICAL_PATH_EVIDENCE.json',detail)
        evidence=[]
        for rel in ['scripts/prepare_sector_network.py','scripts/prepare_network.py','scripts/solve_network.py']:
            data=subprocess.check_output(['git','show',UPSTREAM+':'+rel],cwd=root)
            text=data.decode();lines=text.splitlines()
            ranges={'scripts/prepare_sector_network.py':[(351,381),(506,524),(686,699),(1408,1500),(3601,3667)],'scripts/prepare_network.py':[(i+1,min(i+28,len(lines))) for i,l in enumerate(lines) if l.startswith('def add_co2limit')], 'scripts/solve_network.py':[(i+1,min(i+26,len(lines))) for i,l in enumerate(lines) if l.startswith('def add_co2_sequestration_limit')]}[rel]
            evidence.append(dict(code_sha=UPSTREAM,path=rel,blob_sha256=hashlib.sha256(data).hexdigest(),excerpts=[dict(start=a,end=b,lines=['%d: %s'%(i+1,lines[i]) for i in range(a-1,b)]) for a,b in ranges]))
        write(out/'DEC_UPSTREAM_CODE_EVIDENCE.json',evidence)
        prepared=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/costs_2050_sec.csv')
        # Source recovery is optional off-host; never promote an absent source to verified.
        source_receipt=dict(prepared_cost_path=str(prepared),prepared_cost_expected_sha256=pending[0]['source'],available=prepared.is_file(),role='REVIEW_PROVENANCE_NOT_GATE6_RUNTIME_DEPENDENCY')
        if prepared.is_file():
            import pandas as pd
            source_receipt['actual_sha256']=sha(prepared);assert source_receipt['actual_sha256']==pending[0]['source']
            costs=pd.read_csv(prepared,index_col=0)
            source_receipt['selected_rows']=costs.loc[['gas','SMR','SMR CC','electrolysis','fuel cell','Fischer-Tropsch'],['efficiency','CO2 intensity']].replace({np.nan:None}).to_dict('index')
        local_sources=['scripts_project/build_research_assets.py','scripts_project/carbon_architecture.py','config.default.yaml',
            'research/04_model_assembly/gate4/GATE3_PRODUCTION_FRAGMENT_MANIFEST.json',
            'research/04_model_assembly/gate4/PHYSICAL_VS_POLICY_CARBON_QUALIFICATION.csv',
            'research/04_model_assembly/gate3/evidence/phase3_design/CARBON_SCOPE_FREEZE.md']
        source_receipt['local_evidence']={p:sha(root/p) for p in local_sources}
        source_receipt['builder_lines']='build_research_assets.py:193-211; pending None/False explicitly created; effective config cc_fraction read; no missing gas coefficient'
        write(out/'DEC_SOURCE_RECOVERY.json',source_receipt)
        summary=dict(status='COMPLETE_SOURCE_AND_PENDING_METHOD_REVIEW',review_code_sha256=sha(Path(__file__)),production_weights_written=0,policy_enabled=False,
            item_count=len(rows),by_technology=dict(Counter(r['Technology'] for r in rows)),
            primary_classification={k:sum(r['Classification']==k for r in rows) for k in ['SOURCE_SUPPORTED_MAPPING','SHARED_USE_METHOD_REQUIRES_DECISION','MISSING_OR_CONTRADICTORY_EVIDENCE']},
            source_supported_physical_mappings=sum(r['PhysicalFactClassification']=='SOURCE_SUPPORTED_MAPPING' for r in rows),
            decision_families={'F1_H2_SHARED_POOL':200,'F2_CAPTURE_RECYCLE_ATTRIBUTION':100},families_overlap=True,
            physical_global_counts=dict(h2_stores=int(n.stores.carrier.eq('H2').sum()),direct_h2_loads=int(n.loads.carrier.eq('H2').sum()),
                captured_co2_stores=int(n.stores.carrier.eq('co2 captured').sum()),sequestered_co2_stores=int(n.stores.carrier.eq('co2 sequestered').sum()),
                DAC_links=int(n.links.carrier.str.contains('DAC|direct air',case=False,na=False).sum()),
                sequestration_links=int(n.links.carrier.str.contains('sequestr|geological',case=False,na=False).sum())),
            hashes={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name.startswith('DEC_') and p.name!='DEC_REVIEW_SUMMARY.json'},solver_calls=0,presolve_calls=0,model_builds=0)
        write(out/'DEC_REVIEW_SUMMARY.json',summary);return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();print(json.dumps(run(Path(__file__).resolve().parents[1],args.output),indent=2))
