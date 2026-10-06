import sys,unittest,tempfile,json
from pathlib import Path
from unittest.mock import Mock,call
import requests
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from _osm_download_retry import download_file,ExternalOSMDownloadError
class Response:
    def __init__(self,data=b'pbf bytes',length=None):self.data=data;self.headers={'Content-Length':str(len(data) if length is None else length)}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def raise_for_status(self):pass
    def iter_content(self,chunk_size):yield self.data
class DownloadTests(unittest.TestCase):
    def test_retry_then_verified_cache_no_request(self):
        with tempfile.TemporaryDirectory() as d:
            get=Mock(side_effect=[requests.Timeout('external outage'),Response()]);sleep=Mock()
            path=download_file('https://example.org/a.pbf',d,get=get,sleep=sleep)
            self.assertEqual(get.call_count,2);self.assertEqual(Path(path).read_bytes(),b'pbf bytes')
            fail=Mock(side_effect=AssertionError('must use verified cache'))
            self.assertEqual(download_file('https://example.org/a.pbf',d,True,get=fail),path)
    def test_empty_and_truncated_never_substitute(self):
        for response in [Response(b''),Response(b'partial',999)]:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaisesRegex(ExternalOSMDownloadError,'EXTERNAL_OSM_SERVICE_FAILURE'):
                    download_file('https://example.org/a.pbf',d,get=Mock(return_value=response),sleep=lambda x:None)
                self.assertFalse((Path(d)/'a.pbf').exists());self.assertFalse(list(Path(d).glob('*.part')))
    def test_corrupt_cache_rejected_and_bounded_outage(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(download_file('https://example.org/a.pbf',d,get=Mock(return_value=Response())));p.write_bytes(b'corrupt')
            get=Mock(side_effect=requests.ConnectionError('outage'));sleep=Mock()
            with self.assertRaises(ExternalOSMDownloadError):download_file('https://example.org/a.pbf',d,True,get=get,sleep=sleep)
            self.assertEqual(sleep.call_args_list,[call(1),call(2)])
            self.assertEqual(get.call_count,3);self.assertEqual(p.read_bytes(),b'corrupt')
if __name__=='__main__':unittest.main()
