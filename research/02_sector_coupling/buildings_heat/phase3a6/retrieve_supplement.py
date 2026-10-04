"""Resolve one official moved PDF and cache a unit convention; no data adoption."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
import urllib.request,json,hashlib
R=Path(__file__).resolve().parent;raw=R/'data/raw'
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60) as z:return z.read(),z.url
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.links.extend(v for k,v in attrs if k=='href')
landing='https://www.st.gov.my/resources/guideline-design-installation-inspection-testing-operation-and-maintenance-water-heater'
records=[]
for sid,name,url in [('MY_GUIDELINE_LANDING','my-guideline-landing.html',landing),('TOE_CONVENTION_INSEE','toe-insee.html','https://www.insee.fr/en/metadonnees/definition/c1355')]:
 p=raw/name
 try:
  if p.exists():b=p.read_bytes();resolved=url
  else:b,resolved=get(url);p.write_bytes(b)
  records.append(dict(source_id=sid,url=url,resolved_url=resolved,file='data/raw/'+name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),access_date='2026-10-02',status='UNVERIFIED'))
 except Exception as e:records.append(dict(source_id=sid,url=url,error=str(e),file='',sha256=''))
b=(raw/'my-guideline-landing.html').read_bytes();parser=Links();parser.feed(b.decode())
links=sorted(set(urljoin(landing,s) for s in parser.links if '.pdf' in s.lower() and 'water' in s.lower()));assert len(links)==1,links
url=links[0];p=raw/'my-water-guideline2016.pdf'
try:
 if p.exists():b=p.read_bytes();resolved=url
 else:b,resolved=get(url);assert b.startswith(b'%PDF');p.write_bytes(b)
 records.append(dict(source_id='MY_WATER_GUIDELINE2016_RESOLVED',url=url,resolved_url=resolved,file='data/raw/'+p.name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),version='GP/ST/No.6/2016; dated2017-04-07; landing published2017-06-13',access_date='2026-10-02',status='UNVERIFIED'))
except Exception as e:records.append(dict(source_id='MY_WATER_GUIDELINE2016_RESOLVED',url=url,error=str(e),file='',sha256=''))
(raw/'SUPPLEMENT_REGISTRY.json').write_text(json.dumps(records,indent=2),encoding='utf8');print(json.dumps(records,indent=2))
