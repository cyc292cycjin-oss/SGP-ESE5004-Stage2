"""Build the six freeze deliverables from recorded Git evidence, without Git writes."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parent;E=R/'evidence';BASE=R.parents[2]
def read(n):return json.loads((E/n).read_text(encoding='utf-8-sig'))
def write(n,t):(R/n).write_text(t.rstrip()+'\n',encoding='utf8')
def table(headers,rows):
 return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(c).replace('\n','; ').replace('|',' / ') for c in row)+' |' for row in rows])
U='a3616a68ee44592af6527ca9024a90f1956646ae'
W=read('WSL_BEFORE.json');B=read('REFS_BEFORE.json');I=read('INTEGRITY.json');A=read('AUDIT_SUMMARY.json');M=read('MILESTONES_AFTER.json');P=read('PUSH_PLAN.json');V=read('REMOTE_VERIFICATION_ROWS.json');AF=read('ARCHIVE_FAMILIES.json')
URL='https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2'
archive='753ff15b45ddb91c406a823f8252fc7b603f29c4'
unsafe=[
 ('research/00_model_audit/input_snapshot/data/industry/us_cities.csv','b1165513d87cd4ff809fd75a4bdf64f74602795d','4,081,899','U下载脚本指向Simplemaps Basic v1.93；现有副本仅hash，尚无与来源ZIP的身份/许可对应证明。本轮固定URL返回403。网站产品页称Basic为CC BY 4.0，通用许可页却有不同限制，不能靠字段与URL推定现有字节适用哪一份条款。'),
 ('research/00_source_provenance/official/technology-data/inputs/data_sheets_for_renewable_fuels.xlsx','f41a96401278bf4a50acf2ef09dcb4834791b40e','1,129,971','含xl/media/image1.png、image2.png；原数据身份已知，但DEA通用复制条款排除图片。当前无这些嵌入媒体的单独授权证据。'),
 ('research/00_source_provenance/official/technology-data/inputs/technology_data_catalogue_for_energy_storage.xlsx','bf686797d7c72c296536b7709ef8c21ffe732a07','307,918','含xl/media/image1.png；同上，整工作簿上传的媒体许可尚未关闭。'),
 ('research/00_source_provenance/official/technology-data/inputs/technology_data_for_el_and_dh.xlsx','ce07675ba570a3b6376910505bd2bebcf163c0ba','707,234','含xl/media/image1.png；同上。'),
]
write('SAFETY_REVIEW.md',f'''# Remote publication safety review

审计日期：2026-10-04。结论：12个工程/参考ref允许推送；完整研究归档ref保持 **HOLD — FILE_RIGHTS_UNRESOLVED**。这是本轮上传规则的执行判断，不是认定历史使用违法，也不否定科学结果。

## 范围与方法

在推送前，以origin已有分支为排除集，枚举8个候选分支和14个里程碑的新增可达历史对象，包含后来删除或改写的blob。扫描 **{A['new_blobs']}个新增blob，{A['new_blob_bytes']:,}字节**；最大为DATA_LEDGER.csv 7,162,387字节，新增对象无大于10MB文件。完整对象列表在evidence/NEW_REACHABLE_OBJECTS.json；每ref的对象集合在CANDIDATE_REFS.json，供复核真实归属，不能将同内容blob的所有别名误当作每个ref都有该路径。

检查大小、原始/二进制文件、NetCDF/ZIP/天气cutout/环境目录、常见token/私钥/凭据赋值模式、通信标签。受检新增对象没有发现token/私钥，没有NetCDF、9.9GB作者包、weather cutout或本地环境缓存。有限模式扫描不是零泄漏的普遍证明。原有远程历史未重新发布或改写。

通信匹配9项经定位分别为8个git format-patch头、1份用户基础设施任务书中的`Subject`写作要求。不是导师私人邮件正文。任务说明与公开源码中`private communications`来源标记不能混同实际私有通信。没有据此制造隐私阻断。

## 暂缓归档的精确文件

{table(['Path','Git blob','Bytes','Reason'],unsafe)}

上述文件在真实研究链最早的基线审计状态已经存在，后续Phase3A/B/C和health分支均继承。仅在HEAD删文件仍会上传历史blob，因此本轮没有删除、过滤历史、生成替代合并或偷偷跳过风险。

## 原始条款核查

- [固定technology-data README](https://github.com/PyPSA/technology-data/blob/ec22a1843632fd28ecb9a139ee5156faf23324a3/README.md)明确GPL针对脚本，输入数据可有不同条款。原文保存于evidence/license_review/TECHNOLOGY_DATA_README.txt。
- [DEA数据政策](https://ens.dk/om-os/datapolitik)：允许署名、不歪曲的材料复制；图片、图示、插图与logo另需许可。本轮只读ZIP目录确认嵌入媒体存在，不推定其单独许可。
- [Eurostat政策](https://ec.europa.eu/eurostat/help/copyright-notice)：统计数据一般允许署名复用，仍有第三方等例外。本轮没有把Eurostat工作簿单独认定为阻断项；整个归档已因上表暂缓，不宣称所有二进制都违法。
- [Simplemaps产品页](https://simplemaps.com/data/us-cities)和[通用条款](https://simplemaps.com/data/license)均于本轮只读核查；前者标Basic CC BY 4.0，后者描述不同使用/发布条件。源码固定URL是`https://simplemaps.com/static/data/us-cities/1.93/basic/simplemaps_uscities_basicv1.93.zip`。取证收到HTTP403，未进行数据替换。精确响应在evidence/license_review/CITY_SOURCE_CHECK.json。

## 安全部分与未完成部分

已推12个ref的新增历史只含源码、配置、测试、文档和有意提交的合成/离线验证记录；它们没有继承上表4个blob。这些验证记录是工程审阅证据，不是新增运行或本地缓存倾倒。已有main中的上游输入未变。

归档暂缓符合用户本轮第10节要求。若要完成备份，最小处理是确认这4份既有文件适用于私有研究远端的保存授权，或另行批准一种不改写原史的分离存档方案。不能仅删除最新树中的文件后再推其祖先。代码LICENSE不能代替数据许可，也不因GitHub仓库私有就自动忽略用户明确的上传规则。
''')
write('PRE_PHASE4_GIT_STATE.md',f'''# Pre-Phase4 Git state

实际GitHub项目：{URL}（private，default branch=main，账户push权限已读确认）。状态记录时间：{W['utc']}。证据：WSL_BEFORE.json、REFS_BEFORE.json、INTEGRITY.json、REPOSITORY.json。Windows交付仓库与WSL模型仓库是两个Git历史，不能把Windows HEAD当成模型SHA。

## 远程、对象完整性与工作树

远程main在操作前/后均为 **{U}**。原远程3个分支、0个tag；本地有26分支、12个上游版本tag。没有推送那些无关版本tag。

```text
{W['remotes']}
```

`git fsck --full`退出0，无missing/corrupt对象；4个dangling commit是已有贡献者README/锁环境机器人历史，详见DANGLING_REVIEW.json，无一是本轮14个关键里程碑。它们没有删除，也没有为其制造研究归档ref。此前`--no-reflogs`的12个dangling与本轮4个并不矛盾：可达性根集合不同。

count-objects仍提示worktrees/research_audit/refs下4KiB garbage（准确路径见INTEGRITY.json）。它不等于丢失对象，本轮不清理共享对象库。

{table(['Worktree','Branch','HEAD','Status'],[[x['path'],x['branch'],x['head'],'445 D：既有--no-checkout对象池' if x['path'].endswith('/model-source') else ('CLEAN' if not x['status'] else x['status'])] for x in W['worktrees']])}

model-source由既有prepare_model_layers.py以clone --no-checkout创建，445个D为该特殊未检出状态；未恢复/提交它们。其他12个工作树原先清洁。Windows初始分支codex/github-health-audit、HEAD600b9bdcf52cbd8a887df5d81706a8c7f3909edb；原有outputs/和work/未跟踪内容保留。新报告在独立infra提交中保存。

## 全部本地分支与操作前未推送数量

数量是相对origin已有分支全部历史的差集，不是仅与origin/main比较；不同分支的数量可能重叠，不能相加作为唯一提交数。

{table(['Local branch','SHA','Unpushed commits'],[[k.removeprefix('refs/heads/'),v,B['unpushed'][k]] for k,v in B['local'].items()])}

## 操作前远程分支与本地tags

{table(['Remote-tracking ref','SHA'],B['origin'].items())}

{table(['Existing local tag','Object SHA'],B['tags'].items())}

对象type、parents、contains与14个里程碑的前后状态均保存于MILESTONES.json/MILESTONES_AFTER.json。没有改模型文件、研究输入、科学结果、main或旧分支的tip。
''')
milestone_rows=[]
for m in M:
 cat='CANDIDATE_FIX' if m['name'] in ['industrial_gdp','carbon_key','buildings_e1_source','buildings_e2_source','buildings_e4_source','shipping_allocation','shipping_target_guard','shipping_final'] else 'IMMUTABLE_REFERENCE'
 milestone_rows.append([m['name'],m['sha'],cat,'; '.join(m['remote_after'])])
write('RESEARCH_MILESTONE_REF_PLAN.md',f'''# Research milestone ref plan and execution

**已执行5个注释tag和7个原有分支推送，12/12精确核验。** 注释tag的object SHA与其指向commit SHA不同，验收使用peeled commit。

{table(['Milestone','Commit SHA','Class','Durable remote reachability'],milestone_rows)}

## 最小ref选择

{table(['Remote ref','Expected commit','Purpose'],[[r['RemoteRef'],r['ExpectedSHA'],r['Purpose']] for r in P])}

E1/E2/E4保留原codex分支名，分支tip包含源修复之后的验证/环境说明；未创建重复fix/*别名。shipping只推最终reviewable分支，其祖先包含两项功能修复。combined validation tag指向记录50a73d8f，源353dec3c作为直接父提交可达；没有把记录SHA冒充被测源码。

注释tag消息包含目的、完整source SHA、2026-10-04上下文和不可重定向要求。未碰撞或移动任何tag。没有设置GitHub服务端tag保护规则；这里的immutable是项目引用政策，不是宣称管理员技术上不能删除它们。

## 另外两类ref

- **RESEARCH_ARCHIVE**：已有coherent分支`codex/github-health-audit` @ {archive}可覆盖全部报告族，无需合成三条漂亮历史。但它继承SAFETY_REVIEW.md的4份原件，暂缓推送。未另造archive/*分支，也未把候选fix分支称为全部报告归档。
- **FUTURE_DEVELOPMENT**：`research/full-sc-baseline`保持PENDING。项目既有设计支持从{U}出发，但用户规定必须先完整冻结Phase1–3历史；当前此门槛未过。

本地codex/paper-reference-5bacad70已有等价immutable tag，本轮不再重复推branch；U的research-sc-main、upstream-sc-baseline与未实施修复的fix-topology亦不重复推送。临时/旧草稿/未命名dangling提交未推送。
''')
familyrows=[[x['family'],x['path'],x['file_count'],x['latest_commit'],'LOCAL ONLY — archive HOLD'] for x in AF]
local_outputs=[]
for p in sorted((BASE/'outputs').glob('*')):
 if p.is_file() and p.suffix.lower() in {'.zip','.bundle'}:
  local_outputs.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(E/'LOCAL_ONLY_PACKAGES.json').write_text(json.dumps(local_outputs,ensure_ascii=False,indent=2),encoding='utf8')
write('PHASE1_3_REMOTE_ARCHIVE.md',f'''# Phase1–3 remote archive coverage

**PARTIAL：14个指定/发现的模型与修复里程碑均已远程可达；完整Phase1–3报告链仍仅在本地。** 不能据12个ref核验通过就宣称整个研究史已冻结。

## 已保存远程历史

- tutorial：原`sgp-stage2-asean`和新`reference/tutorial-ce327bfa`。
- paper实际运行、后续publication和U：三个reference tags。
- GDP、carbon、E1/E2/E4、combined buildings、shipping候选：7个原有codex分支；combined buildings另有reference tag。
- 工程验证记录与源码：可从上述分支读取；353dec3c及源修复提交在祖先链中，不依赖reflog。

## 真实研究报告链

`codex/github-health-audit` @ {archive}位于U之上的15个提交，含Phase2基线附带的早期model/source audit，到Phase3C与health审计的连续研究历史。各中间阶段分支都是该历史中的具名检查点。没有为整齐命名合成merge。

{table(['Family','Repository path','Files at archive HEAD','Latest touching commit','Remote status'],familyrows)}

15族路径均在归档HEAD真实存在。文件清单与最近修改commit来自git ls-tree/log，见ARCHIVE_FAMILIES.json；实际提交链见ARCHIVE_CHAIN.json。目录统计为递归范围，Buildings根目录包含其后续子阶段，registry也属于Phase2，数量不能相加作为唯一文件总数。没有自动把未提交文件加入归档。

## 为什么完整归档仍未推送

SAFETY_REVIEW.md列出的4份原件存在于归档的祖先历史。所有承载这些报告族的后续本地审计分支也继承它们，单独推Phase3C等并不能规避。远程当前没有RESEARCH_ARCHIVE类ref。用户要求有风险文件就停止该ref，因此不删除历史、重写commit或偷偷过滤后推送。

## 重要本地交付包

{table(['Local file','Bytes','SHA256'],[[x['path'],x['bytes'],x['sha256']] for x in local_outputs])}

这些ZIP/bundle属于本地交付封装，未上传Git；不等于包内每份报告都缺Git历史。原始大文件、作者results-asean-paper-v1.zip、网络/天气/环境缓存仍按既有manifest/URL/hash引用，不为了远程完整性上传数据字节。未对整个work/递归爬取或复制。当前包的本地性与报告历史的待备份状态分开报告。
''')
write('PHASE4_GIT_STARTING_POINT.md',f'''# Phase4 Git starting point — pending archive completion

**Branch creation=PENDING。`research/full-sc-baseline`本地/远程均未创建。实际parent SHA不存在。** 用户要求先完整冻结Phase1–3历史，目前完整报告链因4份原件的上传许可未关闭而暂缓，故没有跳过前置门槛。

## 两个候选基点的明确评估

| Candidate | SHA | Assessment |
| --- | --- | --- |
| Frozen U | {U} | 与既有Phase3C PHASE4_ASSEMBLY_HANDOFF.md、Phase2 BASELINE_ARCHITECTURE.md一致：U为组装基点，后续选择性集成候选。当前推荐起点。 |
| 已验证Buildings源码 | 353dec3c83b859eab39bcf2dff79fe30d88a2ec0 | 仅Buildings组合验证，不是全部Full-SC工程集成；不能默认为包含GDP、carbon、shipping或最终研究需求边界。 |
| Buildings验证记录tip | 50a73d8f531132c5459174a55cac412d5f684462 | 上一行源码的子提交，仅附验证记录；也不是全系统已验证基点。 |

**完整备份后建议使用的base SHA：{U}**。这是显式建议，不伪造已经创建的分支/parent。现有`codex/research-sc-main`仍在U。新开发ref创建时应直接指向U，不制造“空提交”；此时branch tip=chosen base，Git commit自身的parents仍是U原有parents。

## 未合入的候选

GDP a7a8f06b43f0dcce0dbd7005b989d8f73d142b81；carbon key 753ac81c23f8b9a1ca8ceed531d0630b56f6953d；Buildings E1/E2/E4源修复及组合验证；shipping 512c6cc2e53c579976d269486a7e328a0f372017、cf4b0f816086470dce40ec950e20c045044eec0c和字节保真85a32dc231458fd753445df38d422b78435b8aad。全部是Phase4选择性评审对象，不因远程备份就视为已验收/合入。

immutable tags：reference/tutorial-ce327bfa、reference/paper-run-5bacad70、reference/paper-publication-99159edb、reference/upstream-sc-a3616a68、reference/buildings-validation-50a73d8f。完整SHA见RESEARCH_MILESTONE_REF_PLAN.md和REMOTE_REF_VERIFICATION.csv。

远程archive ref：**尚无完整研究归档ref**；待保存的真实分支为codex/github-health-audit @ {archive}。

远程main：{U}，未改。CodeQL：**EXTERNAL_INFRASTRUCTURE_EXCEPTION / CODEQL_BLOCKS_PHASE4=NO**，沿用已核实的分析完成、SARIF因私有仓库功能不可用而上传失败结论。本轮未改workflow、账号套餐、仓库可见性或安全上传。

本轮scientific/model modifications=0，model assembly=0，solver runs=0，cherry-picks=0，merges=0。当前NO是远程存档门槛，不能据此否定Phase3科学设计关闭，也不能反过来宣称已经准备好正式求解。
''')
write('GITHUB_REMOTE_FREEZE_READINESS.md',f'''# GitHub remote freeze readiness

**安全部分已完成；完整研究历史冻结尚未完成。** 已推送5个注释tag、7个原有工程/验证分支，重新fetch --prune --tags后12/12一致；14个关键里程碑全部可达。完整研究报告链因4份既有原件的上传许可未闭合而暂缓。依据用户前置条件，未创建Phase4分支。

| Status | Value |
| --- | --- |
| GIT_OBJECT_INTEGRITY | PASS |
| PHASE1_3_REMOTE_HISTORY_FROZEN | NO |
| REMOTE_MAIN_UNCHANGED | YES |
| CODEQL_BLOCKS_PHASE4 | NO |
| PHASE4_BRANCH_READY | NO |
| GITHUB_READY_FOR_PHASE4 | NO |

## A–L逐项答复

**A. 对象完整性？** PASS。fsck --full返回0，无missing/corrupt；4个已有bot dangling与4KiB metadata garbage已说明，未删。

**B. main？** 未变，始终{U}；无merge/reset/rebase/force push。

**C. 关键提交是否全部远程可达？** 14个指定/发现的源码、参考和工程里程碑：是。全部Phase1–3报告提交：否，15个研究归档提交仍仅本地。两者不能合并称“全部完成”。

**D. 新标签？** reference/tutorial-ce327bfa、reference/paper-run-5bacad70、reference/paper-publication-99159edb、reference/upstream-sc-a3616a68、reference/buildings-validation-50a73d8f；均为annotated，不是强制的服务器不可变保护。

**E. 工程/验证分支？** codex/fix-industrial-gdp、codex/fix-carbon-config、codex/buildings-e1、codex/buildings-e2、codex/buildings-e4、codex/buildings-accounting-validation、codex/transport-shipping-reviewable-patch。复用原名，无合并。

**F. 完整研究archive ref？** 无。实际coherent分支codex/github-health-audit @ {archive}已识别，但暂缓。

**G. 仍仅本地的材料？** model/source audit、Phase2、Buildings3A1–A7、Transport3B1–B2、Phase3C、health报告链和来源登记，以及本地ZIP封装/原件缓存。工程分支已有自己的验证记录，不能笼统称所有工程证据都未保存。逐族、逐包清单见PHASE1_3_REMOTE_ARCHIVE.md。

**H. 有意不推送？** 有，完整audit/archive分支及等价继承分支。精确路径：`research/00_model_audit/input_snapshot/data/industry/us_cities.csv`，及`research/00_source_provenance/official/technology-data/inputs/`下`data_sheets_for_renewable_fuels.xlsx`、`technology_data_catalogue_for_energy_storage.xlsx`、`technology_data_for_el_and_dh.xlsx`。原因是副本许可/嵌入媒体条款未闭合，不是发现token，不是文件过大。没有安全自动审批拒绝；是执行用户第10节规则。

**I. CodeQL？** 仍只记录EXTERNAL_INFRASTRUCTURE_EXCEPTION。用户已明确接受，CODEQL_BLOCKS_PHASE4=NO；未再次尝试修复或绕过。

**J. Phase4分支已建？** 否，待完整研究史安全冻结。

**K. parent精确SHA？** 分支不存在，故无实际parent。既有设计支持的建议基点为{U}，尚未以新ref执行。

**L. 是否含新科学修改？** 无Phase4分支，无模型内容修改、数据修复、配置更改、集成或求解。本轮仅Git ref备份与审计报告。

## 需要的最小后续处理

1. 对上面4个既有原件确认此私有仓库备份适用的许可/保存授权；城市表固定Basic v1.93源包本轮返回403，已有源码URL与hash保留。DEA数据复制条款与嵌入媒体例外详见SAFETY_REVIEW.md。
2. 若不允许原件进入远程，另行批准保留原史的分离备份方案；本轮不重写commit。仅新增删除提交不能阻止祖先blob被上传。
3. 风险关闭后，推送真实archive分支并重新做reachability验证；然后才从显式U基点创建research/full-sc-baseline。届时仍不自动开始模型组装。

## 证据边界

直接读取：Git对象/refs/parents、13工作树状态、官方API、文件容器/大小、fetch后remote refs。执行判断：按用户规则暂缓有未解决许可问题的archive ref。未证明：所有数据科学验收、完整paper reproduction、Full-SC验证、正式实验可行性。所有科学确认状态保持原样。
''')
write('README.md','''# Pre-Phase4 remote freeze — 2026-10-04

入口：[最终状态与A–L答复](GITHUB_REMOTE_FREEZE_READINESS.md)。

1. [PRE_PHASE4_GIT_STATE.md](PRE_PHASE4_GIT_STATE.md)
2. [RESEARCH_MILESTONE_REF_PLAN.md](RESEARCH_MILESTONE_REF_PLAN.md)
3. [PHASE1_3_REMOTE_ARCHIVE.md](PHASE1_3_REMOTE_ARCHIVE.md)
4. [REMOTE_REF_VERIFICATION.csv](REMOTE_REF_VERIFICATION.csv)
5. [PHASE4_GIT_STARTING_POINT.md](PHASE4_GIT_STARTING_POINT.md)
6. [GITHUB_REMOTE_FREEZE_READINESS.md](GITHUB_REMOTE_FREEZE_READINESS.md)

补充：[暂缓文件与依据](SAFETY_REVIEW.md)。evidence目录保留操作前对象/refs、已公布推送计划、原子push回执、fetch记录与精确核验，未包含原始风险数据。

12个ref备份完成，完整研究报告链备份未完成。CSV由artifact-tool从记录的真实remote/fetched结果生成，未把blocked计划伪装成PASS行。脚本仅针对本轮基础设施，push_verified_refs.py为有防重复检查的一次性操作；不要未经检查重跑。
''')
print(json.dumps({'reports':6,'additional':['README.md','SAFETY_REVIEW.md'],'csv_rows':len(V),'local_packages':len(local_outputs)}))
