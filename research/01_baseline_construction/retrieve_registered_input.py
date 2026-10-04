"""Explicit single-source retrieval to staging, with a separate identity receipt.

Never downloads a latest version, overwrites an existing file, confirms a dataset,
or changes the model's data paths. Unknown source hash remains UNVERIFIED.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, urllib.request

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for x in ['source-id','url','version','destination','max-bytes']:p.add_argument('--'+x,required=True)
    p.add_argument('--expected-sha256')
    a=p.parse_args()
    if not a.url.startswith('https://'):raise ValueError('Use an explicit HTTPS source URL')
    target=Path(a.destination).resolve();part=target.with_suffix(target.suffix+'.part');receipt=target.with_suffix(target.suffix+'.source.json')
    if any(x.exists() for x in [target,part,receipt]):raise FileExistsError('Refusing to overwrite existing source or receipt')
    target.parent.mkdir(parents=True,exist_ok=True)
    info={'source_id':a.source_id,'url':a.url,'version':a.version,'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'filename':str(target),'status':'UNVERIFIED','expected_sha256':a.expected_sha256}
    try:
        h=hashlib.sha256();size=0
        with urllib.request.urlopen(a.url,timeout=60) as src,part.open('xb') as dst:
            while block:=src.read(8*1024*1024):
                size+=len(block)
                if size>int(a.max_bytes):raise ValueError('Explicit download size bound exceeded')
                dst.write(block);h.update(block)
        info.update(bytes=size,sha256=h.hexdigest())
        if a.expected_sha256 and info['sha256']!=a.expected_sha256:raise ValueError('Source hash mismatch; partial file retained for diagnosis')
        part.rename(target);info['identity_check']='MATCH' if a.expected_sha256 else 'HASH_RECORDED_NOT_EXTERNALLY_VERIFIED'
    except BaseException as ex:info['error']=f'{type(ex).__name__}: {ex}';raise
    finally:receipt.write_text(json.dumps(info,indent=2),encoding='utf-8')
