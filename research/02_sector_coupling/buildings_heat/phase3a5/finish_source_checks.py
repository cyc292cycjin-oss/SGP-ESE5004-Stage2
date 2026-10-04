"""Bounded PDF/code checks for the E3 evidence report; no model changes."""
from pathlib import Path
import json,hashlib,difflib,ast
from pypdf import PdfReader
import pypdfium2 as pdfium
R=Path(__file__).resolve().parent
raw=R/'data/raw/buildings'
out={}
for name,pages in {'aeo8.pdf':[48,49,82],'aeo8-corrigendum.pdf':None}.items():
    d=PdfReader(raw/name)
    print(name, len(d.pages))
out['AEO8_evidence_locations']={'BAS_assumptions':'PDF48 / printed46; clean cooking/electrification country growth2005-2022',
 'own_use_losses':'PDF49 / printed47; constant latest-data percentages',
 '2050_generation':'PDF82 / printed80 Figure3.25; BAS3036.3TWh',
 'corrigendum':'November2024 PDF3 revises figure on printed80; BAS3036.3TWh unchanged'}
d=pdfium.PdfDocument(raw/'aeo8.pdf')
d[81].render(scale=1.3).to_pil().save(R/'evidence/previews/AEO8_page82.png')
names=['scripts/build_demand_profiles.py','scripts/add_electricity.py','scripts/final_asean_adjustment.py']
out['code_equivalence']={n:len({hashlib.sha256((R/'evidence/source_snapshot'/k/n).read_bytes()).hexdigest() for k in ['P','U','V']})==1 for n in names}
out['normalized_U_V_equivalence']={n:(R/'evidence/source_snapshot/U'/n).read_text(encoding='utf8')==(R/'evidence/source_snapshot/V'/n).read_text(encoding='utf8') for n in names}
diff=[]
for n in names:
    a=(R/'evidence/source_snapshot/P'/n).read_text(encoding='utf8').splitlines(True)
    b=(R/'evidence/source_snapshot/U'/n).read_text(encoding='utf8').splitlines(True)
    diff.extend(difflib.unified_diff(a,b,fromfile='P/'+n,tofile='U/'+n))
(R/'evidence/P_U_DEMAND_CODE.diff').write_text(''.join(diff),encoding='utf8')
out['aeo8_corrigendum_visual_check']={'pdf_page':3,'printed_page_target':80,'BAS_before_TWh':3036.3,'BAS_after_TWh':3036.3,'scope':'Visually checked Figure3.25; total unchanged; not acceptance of model boundary'}
out['functions']={}
for label in ['P','U','V']:
    sub={}
    for name in ['scripts/build_demand_profiles.py','scripts/prepare_sector_network.py','scripts/final_asean_adjustment.py']:
        tree=ast.parse((R/'evidence/source_snapshot'/label/name).read_text(encoding='utf8'))
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='elec_carrier' for t in node.targets):sub['actual_elec_carrier']=ast.literal_eval(node.value)
            if isinstance(node,ast.FunctionDef) and node.name in ['include_electricity_growth','redistribute_industrial_load','add_electricity_distribution_grid','add_residential','add_services','read_demcast_load','build_demand_profiles']:
                sub[node.name]={'path':name,'start':node.lineno,'end':node.end_lineno,'ast_sha256':hashlib.sha256(ast.dump(node).encode()).hexdigest()}
    out['functions'][label]=sub
(R/'data/processed/buildings/BOUNDARY_SOURCE_CHECKS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(out['code_equivalence'])
