"""Bounded atomic downloads for earth-osm; verified cache, never empty fallback."""
import hashlib
import json
import logging
from pathlib import Path
import tempfile
import time
from urllib.parse import urlsplit
import requests

LOG=logging.getLogger(__name__)
class ExternalOSMDownloadError(RuntimeError):pass

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def download_file(url,dir,exists_ok=False,progress_bar=True,*,attempts=3,get=None,sleep=time.sleep):
    """Adapter matches frozen earth_osm.gfk_download.download_file signature.

    Source PBF .md5 verification remains in earth-osm download_pbf. SHA receipt
    additionally protects cached bytes against partial writes/cache corruption.
    A pre-existing unreceipted cache is never trusted solely because it exists.
    """
    target=Path(dir)/Path(urlsplit(url).path).name;receipt=target.with_name(target.name+'.sha256.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    if exists_ok and target.is_file() and receipt.is_file():
        r=json.loads(receipt.read_text())
        if r.get('url')==url and target.stat().st_size>0 and r.get('sha256')==digest(target):return str(target)
        LOG.warning('OSM_CACHE_REJECTED %s',target)
    request=get or requests.get;last=None
    for attempt in range(attempts):
        temp=None
        try:
            with request(url,stream=True,timeout=(15,120)) as response:
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(dir=target.parent,prefix=target.name+'.',suffix='.part',delete=False) as f:
                    temp=Path(f.name)
                    for b in response.iter_content(chunk_size=1024*1024):
                        if b:f.write(b)
                if not temp.stat().st_size:raise ValueError('Empty external response rejected')
                expected=response.headers.get('Content-Length')
                if expected and not response.headers.get('Content-Encoding') and temp.stat().st_size!=int(expected):raise ValueError('Truncated external response')
                record={'url':url,'bytes':temp.stat().st_size,'sha256':digest(temp),'source_md5_check':'earth-osm download_pbf verifies PBF against companion source .md5'}
                temp.replace(target);temp=None
                receipt.write_text(json.dumps(record,indent=2)+'\n')
                LOG.info('OSM_DOWNLOAD_VERIFIED %s sha256=%s',target,record['sha256']);return str(target)
        except (requests.RequestException,ValueError,OSError) as e:
            last=e;LOG.warning('OSM_EXTERNAL_RETRY %s attempt=%s/%s error=%s',url,attempt+1,attempts,e)
            if attempt+1<attempts:sleep(2**attempt)
        finally:
            if temp is not None:temp.unlink(missing_ok=True)
    raise ExternalOSMDownloadError('EXTERNAL_OSM_SERVICE_FAILURE: '+url+'; '+str(last)) from last

def install():
    from earth_osm import gfk_download
    gfk_download.download_file=download_file
