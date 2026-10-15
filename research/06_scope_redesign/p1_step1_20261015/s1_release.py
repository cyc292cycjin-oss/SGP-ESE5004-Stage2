"""S1 cloud release packaging (supplement 02 §1.4): build the tarball, SHA manifest and deployment
plan locally; nothing is uploaded. Follows the D-stage release format (release/ prefix, per-file
SHA256, manifest SHA pinned in the delivery record).

    python s1_release.py            # from this folder; reads the WSL repo via \\wsl.localhost
"""
from pathlib import Path
import hashlib,io,json,os,subprocess,sys,tarfile,time

HERE=Path(__file__).resolve().parent
REPO=Path(r'\\wsl.localhost\Ubuntu\home\jin\research\SGP_ESE5004_Stage2\phase2\research_model')
S1=REPO/'results_project'/'s1'
CODE=['scripts_project/s1_solve.py','scripts_project/v5/__init__.py','scripts_project/v5/kkt_algebra.py','scripts_project/v5/v5_gates.py','scripts_project/v5/V5_CONTRACT.json',
      'scripts_project/country_carbon.py','scripts_project/carrier_architecture.py','scripts_project/assembly_components.py','scripts_project/integrate_surviving_assets.py',
      'scripts_project/scenario_network.py','scripts_project/validation_dynamics.py','scripts_project/network_checks.py','scripts_project/build_research_network.py',
      'scripts_project/s1_candidates.py','scripts_project/sector_adapter.py','scripts_project/daily_resolution.py','scripts_project/build_research_assets.py','scripts_project/price_basis.py',
      'scripts_project/selected_closure.py','scripts_project/asset_survival.py','scripts_project/gate6_execution_context.py','scripts_project/s1_compare.py',
      'configs/research/baseline.yaml','configs/research/integrated.yaml','configs/research/disconnected.yaml','configs/research/composition.json',
      'research_inputs/corridors/cross_border_corridors.csv']
NETWORKS=['results_project/s1/integrated/integrated_365_24h_unsolved.nc','results_project/s1/disconnected/disconnected_365_24h_unsolved.nc',
          'results_project/s1/integrated/integrated_BUILD_RECEIPT.json','results_project/s1/disconnected/disconnected_BUILD_RECEIPT.json',
          'results_project/s1/resolved_config/integrated.json','results_project/s1/resolved_config/disconnected.json']

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    members=[];manifest={};missing=[]
    for rel in CODE+NETWORKS:
        p=REPO/rel
        if not p.exists():missing.append(rel);continue
        b=p.read_bytes();manifest[rel]=dict(sha256=sha(b),bytes=len(b));members.append((rel,b))
    if missing:print(json.dumps(dict(status='RELEASE_NOT_READY',missing=missing),indent=1));return 2
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w:gz') as t:
        for rel,b in members:
            info=tarfile.TarInfo('release/'+rel);info.size=len(b);info.mtime=0;info.mode=0o644;t.addfile(info,io.BytesIO(b))
    blob=buf.getvalue();tar=HERE/'S1_RELEASE.tar.gz';tar.write_bytes(blob)
    man=dict(schema='s1-release-manifest-v1',created_epoch=time.time(),files=manifest,file_count=len(manifest),archive_sha256=sha(blob),archive_bytes=len(blob),
             git_head=subprocess.run(['wsl.exe','-e','bash','-c','cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model && git rev-parse HEAD'],capture_output=True,text=True).stdout.strip().replace('\x00',''))
    (HERE/'S1_RELEASE_MANIFEST.json').write_text(json.dumps(man,indent=2)+'\n',encoding='utf-8')
    delivery=dict(release_manifest_sha256=sha((HERE/'S1_RELEASE_MANIFEST.json').read_bytes()),archive_sha256=man['archive_sha256'],archive_bytes=len(blob),payload_files=len(manifest),status='PACKAGED_NOT_UPLOADED',cloud_authorization='S1_SUPPLEMENT_01 paused by S1_SUPPLEMENT_02; waiting for new instance host/fingerprint/python path')
    (HERE/'S1_RELEASE_DELIVERY.json').write_text(json.dumps(delivery,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(delivery,indent=1));return 0

if __name__=='__main__':sys.exit(main())
