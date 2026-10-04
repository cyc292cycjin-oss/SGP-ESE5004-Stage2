"""Fetch pinned cost sources and read ZIP directory via byte ranges; never execute contents."""
from collect_sources import ROOT, fetch, save
import concurrent.futures, html, json, re, urllib.parse, urllib.request, struct, io, zipfile, hashlib

def costs():
    sha=json.loads((ROOT/'official/tech_tag.json').read_text())['object']['sha']
    paths=['config.yaml','scripts/compile_cost_assumptions.py','scripts/retrieve_data_from_dea.py','scripts/_helpers.py','inputs/manual_input.csv','inputs/costs_PyPSA.csv','inputs/data_sheets_for_renewable_fuels.xlsx','inputs/technology_data_catalogue_for_energy_storage.xlsx','inputs/technology_data_for_el_and_dh.xlsx','outputs/costs_2030.csv','outputs/costs_2040.csv','outputs/costs_2050.csv']
    jobs=[('technology-data/'+p,'https://raw.githubusercontent.com/PyPSA/technology-data/'+sha+'/'+p) for p in paths]
    jobs += [('tech_fuels_history.json','https://api.github.com/repos/PyPSA/technology-data/commits?sha='+sha+'&path=inputs/data_sheets_for_renewable_fuels.xlsx&per_page=15'),('earthsec_readme.md','https://raw.githubusercontent.com/pypsa-meets-earth/pypsa-earth-sec/main/README.md')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: out=list(pool.map(fetch,jobs))
    save('COST_FETCH_LOG.json',json.dumps(out,indent=2));print('cost files',len(out),[x for x in out if 'error' in x])

class RangeFile(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.pos=0;self.requests=[];self.cache=[]
        b,start,end,total=self.request('bytes=-131072')
        self.size=total;self.cache.append((start,b))
    def request(self,rng):
        req=urllib.request.Request(self.url,headers={'User-Agent':'ASEAN-Provenance-Audit','Range':rng})
        with urllib.request.urlopen(req,timeout=90) as r:
            if r.status!=206: raise RuntimeError('Byte-range unsupported: status '+str(r.status)+'; stopped without downloading full archive')
            cr=r.headers['Content-Range'];m=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',cr)
            if not m: raise RuntimeError('Invalid Content-Range: '+str(cr))
            a,b,n=map(int,m.groups());data=r.read(b-a+2)
            if len(data)!=b-a+1:raise RuntimeError('Truncated range')
            self.requests.append({'range':rng,'content_range':cr,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            return data,a,b,n
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        return self.pos
    def tell(self):return self.pos
    def read(self,n=-1):
        n=self.size-self.pos if n<0 else min(n,self.size-self.pos)
        if not n:return b''
        for start,b in self.cache:
            if start<=self.pos and self.pos+n<=start+len(b):
                result=b[self.pos-start:self.pos-start+n];self.pos+=n;return result
        b,start,end,total=self.request(f'bytes={self.pos}-{self.pos+n-1}')
        if start!=self.pos: raise RuntimeError('Wrong range returned')
        self.pos+=n;return b

def package():
    h=(ROOT/'official/drive_download_response.html').read_text()
    fields=dict(re.findall(r'name="([^\"]+)" value="([^\"]*)"',h))
    url='https://drive.usercontent.google.com/download?'+urllib.parse.urlencode(fields)
    try:
        f=RangeFile(url)
        with zipfile.ZipFile(f) as z:
            entries=[{'name':i.filename,'size':i.file_size,'compressed_size':i.compress_size,'method':i.compress_type,'crc32':f'{i.CRC:08x}','date_time':i.date_time,'header_offset':i.header_offset} for i in z.infolist()]
            save('RESULTS_ZIP_DIRECTORY.json',json.dumps({'archive_bytes':f.size,'comment':z.comment.decode(errors='replace'),'entries':entries},indent=2))
            small=[i for i in z.infolist() if i.file_size<2_000_000 and i.filename.lower().endswith(('.yaml','.yml','.json','.txt','.log','.md','.csv'))]
            for i in small:
                if '..' in i.filename.split('/') or i.filename.startswith('/'):continue
                save('package_metadata/'+i.filename,z.read(i))
            save('RESULTS_RANGE_LOG.json',json.dumps(f.requests,indent=2))
            print('archive bytes',f.size,'entries',len(entries),'small metadata files',len(small));print(json.dumps(entries[:12],indent=2))
    except Exception as e:
        save('RESULTS_RANGE_ERROR.json',json.dumps({'error':str(e)},indent=2));print('package error:',e)
if __name__=='__main__':
    costs();package()
