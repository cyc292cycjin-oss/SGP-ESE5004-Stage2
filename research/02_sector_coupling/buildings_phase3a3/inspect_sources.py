"""Verify downloaded identities and precise source locations, without adoption."""
from pathlib import Path
import hashlib,json
from pypdf import PdfReader
R=Path(__file__).resolve().parent
M=R/'data/raw/buildings/RETRIEVAL_MANIFEST.json'
manifest=json.loads(M.read_text())
for r in manifest:r['filename']=r['filename'].replace('\\','/')
M.write_text(json.dumps(manifest,indent=2),encoding='utf8')
checks=[]
for r in manifest:
    if r['access']=='RETRIEVED':
        p=R/r['filename'];checks.append(dict(source_id=r['source_id'],sha256_match=hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']))
selections=[('malaysia-neb2016.pdf',92,['2,000','Peninsular']),
 ('malaysia-neb2016.pdf',95,['TABLE 42','70','655','2,875']),
 ('malaysia-neb2016.pdf',98,['Peninsular','5,000']),
 ('malaysia-neb2016.pdf',103,['TABLE 47','GWh','1,034.62','39,106.00']),
 ('eria-commercial2021.pdf',17,['GWh','1,034.62','39,106.00']),
 ('eria-commercial2021.pdf',18,['39,106 ktoe']),
 ('eria-pilot2013.pdf',49,['112','neighbourhood']),
 ('eria-pilot2013.pdf',56,['September 2011','February 2012','Table 11']),
 ('belda-eceee2017.pdf',2,['1,190']),
 ('belda-eceee2017.pdf',6,['less than 1%'])]
locations=[]
for filename,page,terms in selections:
    p=R/'data/raw/buildings'/filename
    text=PdfReader(p).pages[page-1].extract_text()
    found={term:term in text for term in terms}
    locations.append(dict(filename=filename,pdf_page_1_based=page,terms_found=found))
result=dict(identity_checks=checks,locations=locations,
  visual_review=['malaysia-neb2016.pdf:95','malaysia-neb2016.pdf:103','eria-commercial2021.pdf:18'],
  scientific_acceptance='PENDING',derived_model_inputs=0)
processed=R/'data/processed/buildings';processed.mkdir(parents=True,exist_ok=True)
(processed/'SOURCE_LOCATIONS.json').write_text(json.dumps(locations,indent=2))
(R/'evidence/SOURCE_LOCATION_CHECKS.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
