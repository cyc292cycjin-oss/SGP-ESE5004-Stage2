"""Download a bounded set of NetCDF members, verify ZIP CRC, record SHA-256."""
from recover_remote import RangeFile, ROOT, save
import urllib.parse,re,zipfile,json,hashlib,time
def main():
    h=(ROOT/'official/drive_download_response.html').read_text()
    url='https://drive.usercontent.google.com/download?'+urllib.parse.urlencode(dict(re.findall(r'name="([^\"]+)" value="([^\"]*)"',h)))
    f=RangeFile(url);records=[]
    targets=[('baseline-aims-3H','2025'),('decarbonize-aims-3H','2050')]
    with zipfile.ZipFile(f) as z:
        for scenario,year in targets:
            member=next(i for i in z.infolist() if '/'+scenario+'/' in i.filename and '_'+year+'_' in i.filename and i.filename.endswith('.nc'))
            out=ROOT/'cache'/member.filename;out.parent.mkdir(parents=True,exist_ok=True)
            if not out.exists():
                with z.open(member) as src, out.open('wb') as dest:
                    while b:=src.read(8*1024*1024):dest.write(b)
            digest=hashlib.file_digest(out.open('rb'),'sha256').hexdigest()
            records.append({'member':member.filename,'path':str(out.relative_to(ROOT)),'bytes':out.stat().st_size,'sha256':digest,'zip_crc32':f'{member.CRC:08x}','note':'ZIP CRC checked during completed decompression; no model execution'})
            save('RESULTS_MEMBER_HASHES.json',json.dumps(records,indent=2));print('completed',member.filename,flush=True)
    save('RESULTS_MEMBER_RANGE_LOG.json',json.dumps(f.requests,indent=2))
if __name__=='__main__': main()
