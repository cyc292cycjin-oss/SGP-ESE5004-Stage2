"""Read the official Asian weather ZIP directory only, with bounded range I/O."""
from pathlib import Path
import sys,json,zipfile
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'00_source_provenance'))
from recover_remote import RangeFile
url='https://drive.usercontent.google.com/download?id=11-Ax9tVks7oPjrZwG5v3C0x4OmMT_Pv8&export=download&confirm=t'
f=RangeFile(url)
with zipfile.ZipFile(f) as z:
    entries=[{'filename':i.filename,'bytes':i.file_size,'compressed_bytes':i.compress_size,'crc32':f'{i.CRC:08x}','date_time':i.date_time,'method':i.compress_type} for i in z.infolist()]
out={'source_url':url,'archive_bytes':f.size,'entries':entries,'range_requests':f.requests,
     'status':'AVAILABLE_CANDIDATE_NOT_AUTHOR_HASH_VERIFIED','paper_config_cutout_name':'cutout-2013-era5'}
(root/'WEATHER_ARCHIVE_DIRECTORY.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
