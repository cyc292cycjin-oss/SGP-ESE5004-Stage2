"""Windows-only final review ZIP SHA, size, path and CRC verification; no network."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,zlib,datetime
W=Path(r'D:\ResearchWorkspaces\ASEAN\work\c05_aggregate0_20261012')
Z=Path(r'D:\ResearchWorkspaces\ASEAN\outputs\C05_AGGREGATE0_DAILY_DIAGNOSTIC_REVIEW.zip')
P=W/'review_payload'
sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(Z) as z:
 names=z.namelist();assert len(names)==len(set(names))
 assert 'CRC_VALIDATION.json' not in names
 for name in names:
  path=PurePosixPath(name)
  assert not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name
 assert z.testzip() is None
 manifest=json.loads(z.read('DELIVERY_MANIFEST.json'))
 expected={e['relative_path'] for e in manifest['files']}|{'DELIVERY_MANIFEST.json'}
 assert set(names)==expected
 for e in manifest['files']:
  b=z.read(e['relative_path']);assert len(b)==e['bytes'] and sha(b)==e['sha256']
 members=[{'relative_path':i.filename,'bytes':i.file_size,'sha256':sha(z.read(i.filename)),'CRC32':f'{i.CRC:08x}','CRC_verified':(zlib.crc32(z.read(i.filename))&0xffffffff)==i.CRC} for i in z.infolist()]
 assert all(x['CRC_verified'] for x in members)
record={'status':'ZIP_CONTENT_SHA_SIZE_CRC_PASS','checked_before_adding_this_record':members,
 'self_reference_policy':'This record excludes its own CRC. Final external receipt verifies every member including this record and the full ZIP SHA.',
 'solver_calls_during_packaging':0,'bulk_data_included':False}
record_bytes=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()
with zipfile.ZipFile(Z,'a',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('CRC_VALIDATION.json',record_bytes)
(P/'CRC_VALIDATION.json').write_bytes(record_bytes)
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 assert set(z.namelist())==expected|{'CRC_VALIDATION.json'}
 final_members=[{'relative_path':i.filename,'bytes':i.file_size,'sha256':sha(z.read(i.filename)),'CRC32':f'{i.CRC:08x}','CRC_verified':(zlib.crc32(z.read(i.filename))&0xffffffff)==i.CRC} for i in z.infolist()]
 assert all(x['CRC_verified'] for x in final_members)
 git=json.loads(z.read('GIT_PUBLICATION.json'))
receipt={'status':'C05_REVIEW_DELIVERY_COMPLETE','scientific_status':'C05_NUMERIC_NO_SOLUTION_NOT_ACCEPTED',
 'native_status':12,'SolCount':0,'Barrier_iterations':24,'Runtime_seconds':81.59514498710632,
 'zip_path':str(Z),'zip_bytes':Z.stat().st_size,'zip_sha256':sha(Z.read_bytes()),'full_archive_CRC':'PASS',
 'members_count':len(final_members),'all_member_size_SHA_CRC':'PASS','members':final_members,
 'git_commit':git['commit'],'branch':git['branch'],'PR':git['PR'],
 'local_raw_backup':'LOCAL_BACKUP_SHA_VERIFIED','no_more_optimization_authorized':True,
 'completed_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(W/'C05_FINAL_DELIVERY_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='members'},ensure_ascii=False,indent=2))
