"""Export committed C05 lightweight review files; never include run bulk data."""
from pathlib import Path
import json,hashlib,subprocess,datetime
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c05_aggregate0_20261012')
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
OUT=W/'review_payload'
BRANCH='codex/c05-aggregate0-daily-20261012'
PR='https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/15'
def git(*args):return subprocess.check_output(['git','-C',str(R),*args])
assert git('branch','--show-current').decode().strip()==BRANCH
assert not git('status','--porcelain').strip()
head=git('rev-parse','HEAD').decode().strip()
remote=git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
assert remote==head
OUT.mkdir(exist_ok=False)
scopes=['research/05_baseline_evolution/20261011/c05','research/05_baseline_evolution/20261011/BASELINE_EVOLUTION_LEDGER.md','research/05_baseline_evolution/20261011/b03_c00/C00_GO_NO_GO_CHECKLIST.md','research/STAGE2_PROJECT_LEDGER.md']
paths=git('ls-files','-z','--',*scopes).decode().split('\0')
for rel in filter(None,paths):
 data=git('show',head+':'+rel); p=OUT/rel
 assert p.suffix not in ('.npy','.npz','.nc','.lic','.so','.zip','.gz','.pyc')
 assert len(data)<4_000_000
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
meta={'branch':BRANCH,'commit':head,'verified_remote_head':remote,'PR':PR,'related_PRs':[13,14],
      'production_commit':'d6c48dbd95d12f0354561372e9a65d6e92511754',
      'result_and_indexed_log_milestone':'869d72a90376b1862cf2058576b01917131f0a12',
      'exported_from':'committed Git objects, not mutable working files',
      'built_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/'GIT_PUBLICATION.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(OUT/'README.md').write_text(f'''# C05审阅包

状态：C05_NUMERIC_NO_SOLUTION_NOT_ACCEPTED。唯一一次优化：Status12 NUMERIC，SolCount0，24次Barrier，81.595145秒。没有完整合法解，未执行日V4；云端封存及本地SHA备份完成。

主报告：research/05_baseline_evolution/20261011/c05/C05_AGGREGATE0_DAILY_DIAGNOSTIC_RESULT.md。
实际最终提交：{head}；分支：{BRANCH}；PR：{PR}（未合并，关联#13/#14）。

全部成员从该Git提交导出；公开日志只移除许可证注册元数据，原件SHA和修改说明见证据索引。包内没有矩阵、NetCDF、X/Pi/RC、许可证或凭据。

完整新增原始证据目录：D:\\ResearchWorkspaces\\ASEAN\\outputs\\c05_daily_diagnostic\\c05_aggregate0_daily122_20261012T074925Z_a39647d9\\cloud_run。
新增原始归档SHA：4b78d58396be73378ede9589a3bf3db56ad671a9643d82d50da7dd7b1e1bac63，394606字节；历史输入按不可变引用复用。未改写封存时的LOCAL_SYNC_PENDING回执；其后本地备份回执已证明同步完成。

DELIVERY_MANIFEST.json列出内容文件大小和SHA；CRC_VALIDATION.json记录归档内容CRC实测。为避免自引用，清单不包含自身及后加CRC记录；最终全部成员（包括这些元数据）的完整性在外部C05_FINAL_DELIVERY_RECEIPT.json核验。请将此ZIP上传ChatGPT联合审阅。

G6-05保持暂停；C05授权已消费。任何下一次优化均需新的明确授权。122实例保持运行与计费。本包包含历史生产源码供复核，不得把它当成新的运行授权或重复执行入口。
''',encoding='utf-8')
files=[{'relative_path':str(p.relative_to(OUT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.rglob('*')) if p.is_file()]
(OUT/'DELIVERY_MANIFEST.json').write_text(json.dumps({'git_commit':head,'files':files,'exclusions':['DELIVERY_MANIFEST.json (self)','CRC_VALIDATION.json (added after first ZIP CRC verification)'],'bulk_data_included':False},ensure_ascii=False,indent=2)+'\n')
(W/'C05_PACKAGE_STAGE.json').write_text(json.dumps({'git':meta,'payload':str(OUT),'content_files':len(files)},indent=2)+'\n')
print(json.dumps({'payload':str(OUT),'git':head,'content_files':len(files),'content_bytes':sum(x['bytes'] for x in files)}))
