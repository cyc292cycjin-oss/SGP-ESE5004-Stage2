"""Read-only, bounded cached transport inspection; writes audit evidence only.

Run in WSL with --cache the original tutorial checkout. No model imports,
downloads, demand replacement, or solver execution. Numeric values are evidence.
"""
import argparse
import ast
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
import numpy as np

COUNTRIES = ['BN','ID','KH','LA','MM','MY','PH','SG','TH','TL','VN']
NAMES = {'Brunei Darussalam':'BN','Indonesia':'ID','Cambodia':'KH',
         "Lao People's Dem. Rep.":'LA',"Lao People's Democratic Republic":'LA',
         'Myanmar':'MM','Malaysia':'MY','Philippines':'PH','Singapore':'SG',
         'Thailand':'TH','Timor-Leste':'TL','Viet Nam':'VN','Vietnam':'VN'}
FIELDS = ['total road','road electricity','road gas','road biomass','road oil',
          'total rail','electricity rail','total domestic navigation',
          'total international navigation','total domestic aviation','total international aviation']

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--cache',required=True)
    args=parser.parse_args(); cache=Path(args.cache); out=Path(__file__).resolve().parent/'evidence'
    dest=out/'cached_inputs'; dest.mkdir(exist_ok=True)
    evidence={'status':'READ_ONLY_AUDIT_NOT_ACCEPTED_MODEL_INPUT','source_cache':str(cache),
              'country_order':COUNTRIES,'table_unit':'TWh/year (derived model input, not mobility service)',
              'files':[],'tables':{},'raw_rows':[]}
    def record(p,copy=False):
        item={'path':str(p),'exists':p.is_file()}
        if p.is_file():
            item.update(bytes=p.stat().st_size,sha256=sha(p))
            if copy:
                target=dest/p.relative_to(cache); target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,target)
                item['audit_copy']=str(target.relative_to(out.parent))
        evidence['files'].append(item); return item
    resources=cache/'resources/baseline-aims-3H-tutorial'
    for year in ['base','2030','2040','2050']:
        p=resources/f'energy_totals_{year}.csv'; record(p,True)
        data={r['']:r for r in rows(p)}
        evidence['tables'][year]={co:{col:data[co].get(col) for col in FIELDS} for co in COUNTRIES}
    evidence['missing_to_zero']=[{'country':co,'field':col,'base':v,
        'future':{y:evidence['tables'][y][co][col] for y in ['2030','2040','2050']}}
        for co,r in evidence['tables']['base'].items() for col,v in r.items() if v in ('',None)]
    evidence['cagr']={}
    for name in ['growth_factors_cagr','efficiency_gains_cagr','fuel_shares']:
        p=cache/f'data/demand/{name}.csv'; record(p,True); data={next(iter(r.values())):r for r in rows(p)}
        evidence['cagr'][name]={'index':list(data),'asean_country_rows':[co for co in COUNTRIES if co in data],
             'all_asean_use_default':all(co not in data for co in COUNTRIES),
             'default_transport_fields':{k:v for k,v in data['DEFAULT'].items() if any(w in k for w in ['road','rail','navigation','aviation'])},
             'absent_transport_columns':[col for col in FIELDS if col not in data['DEFAULT']]}
    record(cache/'data/demand/unsd/paths/Energy_Statistics_Database.xlsx',True)
    record(cache/'data/demand/unsd/unsd.zip')
    # Fixed direct input directory only. Each raw file is streamed and only
    # 2019 ASEAN road/rail/navigation/aviation records are retained.
    for p in sorted((cache/'data/demand/unsd/data').glob('*.txt')):
        rec=record(p); matched=0
        with p.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f,delimiter=';')
            for row in reader:
                text=row.get('Commodity - Transaction',''); name=row.get('Country or Area')
                if row.get('Year')!='2019' or name not in NAMES: continue
                mode=next((m for m in ['road','rail','aviation','navigation'] if m in text.lower()),None)
                if not mode and 'marine bunkers' in text.lower(): mode='navigation'
                if not mode: continue
                matched+=1; parts=text.split(' - ')
                evidence['raw_rows'].append({'file':str(p),'file_sha256':rec['sha256'],
                    'csv_physical_line_end':reader.line_num,'country':NAMES[name],'mode':mode,
                    'commodity':parts[0],'transaction':parts[1] if len(parts)>1 else '',**row})
        rec['matched_asean_2019_transport_rows']=matched
    # Derive conversion checks solely from the already captured frozen U source.
    tree=ast.parse((out/'source/U/scripts/_helpers.py').read_text(encoding='utf-8-sig'))
    constants={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            key=node.targets[0].id
            if key in ['fuels_conv_toTWh','gas_fuels','oil_fuels','biomass_fuels']:
                try: constants[key]=ast.literal_eval(node.value)
                except (ValueError,TypeError): pass
    for row in evidence['raw_rows']:
        q=float(row['Quantity']); unit=row['Unit']; factor=None
        if unit=='Kilowatt-hours, million': factor=.001
        elif unit=='Terajoules': factor=1/3600
        elif unit in ['Metric tons,  thousand','Cubic metres, thousand']:
            factor=constants['fuels_conv_toTWh'].get(row['commodity'])
        row['audit_source_conversion_factor_to_TWh']=factor
        row['audit_Quantity_TWh']=None if factor is None else q*factor
    def selected(col,row):
        com=row['commodity']; mode=row['mode']; tr=row['transaction']
        if col=='total road': return mode=='road'
        if col=='road electricity': return mode=='road' and com=='Electricity'
        if col.startswith('road '): return mode=='road' and com in constants[col.split()[1]+'_fuels']
        if col=='total rail': return mode=='rail' and com in ['Gas Oil/ Diesel Oil','Biodiesel','Electricity']
        if col=='electricity rail': return mode=='rail' and com=='Electricity'
        location='domestic' if 'domestic' in col else 'international'
        mode='aviation' if 'aviation' in col else 'navigation'
        tx={'domestic':'Consumption by domestic '+mode,'international':'International '+('aviation' if mode=='aviation' else 'marine')+' bunkers'}[location]
        return row['mode']==mode and tr==tx and (mode!='aviation' or com=='Kerosene-type Jet Fuel')
    evidence['raw_country_summary']={}
    evidence['conversion_comparison']=[]
    for co in COUNTRIES:
        subset=[r for r in evidence['raw_rows'] if r['country']==co]
        evidence['raw_country_summary'][co]={m:{'row_count':len([r for r in subset if r['mode']==m]),
          'commodities':sorted(set(r['commodity'] for r in subset if r['mode']==m)),
          'units':sorted(set(r['Unit'] for r in subset if r['mode']==m)),
          'electricity_rows':[r for r in subset if r['mode']==m and r['commodity']=='Electricity']}
          for m in ['road','rail','navigation','aviation']}
        for col in FIELDS:
            selected_rows=[r for r in subset if selected(col,r)]
            v=evidence['tables']['base'][co][col]
            total=float(np.round(np.array([r['audit_Quantity_TWh'] for r in selected_rows if r['audit_Quantity_TWh'] is not None]).sum(),4))
            evidence['conversion_comparison'].append({'country':co,'field':col,'base_text':v,
                'selected_raw_count':len(selected_rows),'audit_sum_TWh':total,
                'matches_nonblank_base':None if v in ('',None) else abs(float(v)-total)<1e-8,
                'blank_is_not_zero':v in ('',None),
                'zero_has_no_selected_raw_row':v not in ('',None) and float(v)==0 and not selected_rows})
    otherpaths=['resources/baseline-aims-3H-tutorial/transport_data.csv',
       'data/temp_hard_coded/transport_data.csv','data/custom/airports.csv',
       'data/ports/wpi_data_download_original.zip','data/ports/wpi_tutorial_from_gdb.csv',
       'data/ports/wpi_tutorial_from_gdb.provenance.json',
       'resources/baseline-aims-3H-tutorial/ports.csv',
       'resources/baseline-aims-3H-tutorial/airports.csv']
    evidence['cached_transport_and_locations']={}
    for rel in otherpaths:
        p=cache/rel; rec=record(p,p.is_file() and p.stat().st_size<1024*1024)
        item={'file':rec}
        if p.is_file() and p.suffix=='.csv':
            data=rows(p); item['all_rows_count']=len(data)
            item['asean_rows']=[r for r in data if r.get('country') in COUNTRIES]
            item['asean_country_counts']=dict(Counter(r['country'] for r in item['asean_rows']))
        if p.is_file() and p.suffix=='.json': item['provenance']=json.loads(p.read_text())
        evidence['cached_transport_and_locations'][rel]=item
    evidence['summary']={'raw_files_scanned':len(list((cache/'data/demand/unsd/data').glob('*.txt'))),
       'raw_transport_rows':len(evidence['raw_rows']),
       'unsupported_unit_or_factor_rows':len([r for r in evidence['raw_rows'] if r['audit_Quantity_TWh'] is None]),
       'blank_base_transport_cells':len(evidence['missing_to_zero']),
       'nonblank_base_comparison_mismatches':[r for r in evidence['conversion_comparison'] if r['matches_nonblank_base'] is False]}
    (out/'CACHED_DEMAND_EVIDENCE.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def table(cols, values):
        return '\n'.join(['|'+'|'.join(cols)+'|','|'+'|'.join(['---']*len(cols))+'|']+
          ['|'+'|'.join(str(v) for v in row)+'|' for row in values])
    base=evidence['tables']['base']
    blank=lambda value:'MISSING' if value in ('',None) else value
    note='''# Cached transport demand evidence (read-only)

Evidence class: direct cache inspection and analytical conversion check; no new accepted input. Cache is the original tutorial checkout, **not** proof that these data entered a sector-coupled solved ASEAN network. Frozen U source SHA is `a3616a68ee44592af6527ca9024a90f1956646ae`.

## Scope and exact evidence

`CACHED_DEMAND_EVIDENCE.json` records every inspected file SHA256, copied small-file path, original raw row and physical line end, year, unit, quantity, footnotes, commodity, transformation factor, and country/mode coverage. `inspect_cached_demand.py` only reads the explicit UNSD input directory and named small inputs; no download, model imports, workflow or solver. All amounts below are cached **annual final-energy TWh**, not passenger-km/tonne-km/vehicle-km or accepted useful mobility service.

52 cached UNSD TXT exports named `UNdata_Export_20250502_*` were streamed; 123 ASEAN 2019 transport records were retained. File names give an export-date clue, not evidence that 2025 is the observation year: all extracted observations are 2019. The cached raw archive, raw files and original link workbook have separate hashes. Source links/download paths: frozen U `build_base_energy_totals.py:366–455` reads the path workbook, can retrieve its URLs, or falls back to Google Drive archive `1VUV0X-tTQECi2pHdE5EWXjPI2yeCdk6F`; the presence of an archive does not prove which historical download branch ran.

## Base transport accounts

The table deliberately preserves missing cells. A displayed 0 can be an empty-commodity-subset sum and is not automatically an observed national zero.

'''
    note+=table(['Country','Road total','Road electricity','Road gas','Road biomass','Road oil'],
        [[co]+[blank(base[co][c]) for c in FIELDS[:5]] for co in COUNTRIES])+'\n\n'
    note+=table(['Country','Rail total','Rail electricity','Domestic navigation','International navigation','Domestic aviation','International aviation'],
        [[co]+[blank(base[co][c]) for c in FIELDS[5:]] for co in COUNTRIES])+'\n\n'
    note+='''## Source units and aggregation

- Source electricity units `Kilowatt-hours, million` become TWh by /1000; `Terajoules` by /3600. Cached transport mass records `Metric tons,  thousand` use the frozen `_helpers.get_conv_factors("industry")` dictionary. All 123 retained rows have a supported conversion. Fuel-factor provenance points to the UN energy balance methodology in code; HHV/LHV acceptance is not established merely by that citation.
- `build_base_energy_totals.py:203–222`: road is the sum of final energy across available commodities; no passenger/freight split. Road electricity is a filtered `Electricity` sum.
- `:246–259`: rail total uses only diesel, biodiesel and electricity; electricity is a subset, not an additional independent total. Do not add `total rail + electricity rail` as separate full demands.
- `:261–290`: aviation uses Kerosene-type Jet Fuel only and distinguishes domestic consumption from international aviation bunkers. Navigation uses all selected commodities and distinguishes domestic navigation from international marine bunkers. Bunkers are a separate named transaction; their assignment to a research national final-energy boundary remains a boundary decision.
- An independent numerical check using NumPy scalar summation/rounding to match pandas-derived rounding reproduces every nonblank cached base cell (107 of 121 transport cells). No model was executed. This verifies consistency with the present cache, not scientific acceptance of factors, completeness, or paper provenance.

## Missing and zero are materially different

1. All 11 `road electricity` cells are `0.0`, but **there is no Electricity-road record for any of the 11 countries in the cached 2019 raw data**. The road-sector subset contains non-electric rows, then `.sum()` over its empty electricity subset returns zero. Therefore these cells cannot establish that historical EV electricity is zero or justify an EV subtraction of zero from A*.
2. Rail electricity records exist for ID, MY, PH, SG and TH. KH and MM have rail fuel rows but no electricity rail rows: their rail-electricity 0 is another empty-subset sum. BN, LA, TL and VN have no rail rows and base rail fields are missing.
3. There are 14 blank base transport cells: both rail fields for BN/LA/TL/VN (8) and domestic/international navigation for BN/LA/TL (6). All become `0.0` in the cached 2030/2040/2050 tables. `prepare_energy_totals.py:296` explicitly performs `fillna(0)` on output. This is missing-to-zero engineering behavior, not verification of absent demand.
4. In addition, growth and efficiency input tables omit `road electricity`, `road gas`, `road biomass`, and `road oil` columns. Column-aligned multiplication (`prepare_energy_totals.py:108–112`) creates missing values for these subaccounts; all four become zero in future output even when base gas/biomass/oil are positive. Thus these future columns are not valid historical account evidence and do not show that future road fuel demand disappeared; the separate total road remains.

## Projection defaults

Every ASEAN country is absent from both growth and efficiency CAGR country indices and therefore inherits `DEFAULT`; the fuel-shares table likewise has no ASEAN rows. This is directly demonstrated in `cagr` JSON. Do not label the generic default as an ASEAN forecast, or assume a European geographic calibration that the table itself does not prove. The actual geographic calibration is unverified.

`prepare_energy_totals.py:260–289` overwrites road and navigation totals with share-weighted technology-specific efficiency projections times growth. Accordingly, the presence of generic `total international navigation = 0.2742` in the efficiency CAGR file does **not** mean the final navigation value uses that rate: the later override uses `total navigation oil` / `total navigation hydrogen`.

'''
    note+=table(['Default parameter','Growth CAGR','Efficiency CAGR'],
      [[field,evidence['cagr']['growth_factors_cagr']['default_transport_fields'].get(field,'NO COLUMN'),
        evidence['cagr']['efficiency_gains_cagr']['default_transport_fields'].get(field,'NO COLUMN')]
       for field in ['total road','total rail','electricity rail','total domestic aviation','total international aviation','total domestic navigation','total international navigation','total road ev','total road fcev','total road ice','total navigation oil','total navigation hydrogen']])+'\n\n'
    note+='''## Vehicle and location caches

- `resources/baseline-aims-3H-tutorial/transport_data.csv` does **not** exist. This bounds the evidence: it does not prove no other checkout generated such a file. The inspected original tutorial cache does not contain the prepared vehicle input.
- `data/temp_hard_coded/transport_data.csv` exists, SHA256 `360a8812c03e42c823e5a45665e9dd9a802228594b1dc79ea095e5d87612d3b7`, 183 rows including all 11 countries. `number cars` and `average fuel efficiency` have no per-row source/year metadata. Source code describes WHO registered vehicles plus Wikipedia completion, World Bank fuel data and fallback. These cached values must not be presented as verified ASEAN passenger-car stock or country-specific vintage; the current units/source semantics need their producer trace. This audit performs no external refresh.
- Tutorial ports have explicit engineering provenance: user export from the official NGA WPI viewer on 2026-09-29, then field mapping from GDB. Raw ZIP SHA256 `34461849e406f2b1fc92009dd928e2f35785ddf1549971c397b4eddfc873e224`; converted full CSV SHA256 `c86b548f5a214649f2f2b16e700986824ee8dbd9d6451a5195514fc7846d7d19`. The copied provenance says **tutorial engineering test only; not verified as author paper input**. Current upstream's monthly WPI URL must not be substituted for this actual cache lineage.
- Tutorial `ports.csv` SHA256 `a54d323763faf5419cbc4095aaec8dca1670380d39e72ef98436b4ec89c7f28c` and `airports.csv` SHA256 `51a80a016c635fbf60665c6262abc8d334febffa79d1bf291952ff2ca400bf6e` are retained as small copies. ASEAN country row counts and actual rows are in JSON. No Lao port row is observed; that should be resolved against selected bunker/domain geography, not auto-filled.
- Airport producer points to live OurAirports airports/runways files, but the exact raw source version/archive was not located in this bounded cache inspection. The processed file hash freezes what exists, not its upstream release. `data/custom/airports.csv` is also copied and hashed; its presence alone is not proof that the effective tutorial switch selected it.

## Review implications

Verified cache gaps that matter: missing-versus-zero transport electricity, loss of future road subaccounts, generic projections, and large separately reported international bunker accounts. The existing cached inputs support a bounded transport audit, not an accepted new demand scenario. National EV stock microdetail is not required merely to acknowledge these accounting issues. No values were patched and no missing demands were constructed.
'''
    (out/'CACHED_DEMAND_NOTES.md').write_text(note,encoding='utf-8')
    print(json.dumps(evidence['summary'],ensure_ascii=False))

if __name__=='__main__': main()
