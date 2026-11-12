### V5 X20 C 段（决策 252、253：水电候选单位入流、陆上风电格点内分档、X21 参照水平开关）— 2026-11-12

- **起因：** 审阅端验收 B 段（决策 252：B 段通过，偏离接受；PR 等独立审查后再建；`cache/v4solved` 保留）。冻结前做两项修正：C-1（L-C10）直接实施；C-2（L-C11）先写规格（`X20_C2_ONWIND_SUBGRID_SPEC.md`）。审阅端确认时补充：门槛只对候选潜力 ≥ 1 GW 的国家设置，在结果之前写入规格（`72272498`）。
- **C-1（`b9852d22`）：** 新建水电候选每 MW 年入流 = 国别目标（Ember 中位数 × 1.1）÷ Ember 国别装机中位数，11 国统一，存量不变。开关 `hydro_candidate_unit_inflow`。新建水库 CF：ID 0.706 → 0.594、MY 0.651 → 0.644、VN 0.570 → 0.456、PH 0.469 → 0.415（B 段 → C-1）。
- **C-2（`9622c78d`）：** 每个 ERA5 格点取 GWA 像元风速比的 10 个等面积档，格点 CF = 档 CF 的面积加权平均；风场校准与 α 不变。开关 `onwind_subgrid`。
  - 预检未通过：10 个适用国家为 0.555–0.744，均 < 0.8。
  - 审阅端决策 253：仍采用 quantile10 为主值，不改参数与区间，理由是参照按固定 CF 比例外推、模型按固定风速比例外推。
  - 最终网络主标准 0.507–0.781；按等级看，最好等级多为 0.72–1.12，差距集中在最差等级。
- **X21 开关（`9622c78d`、`645c37e9`）：** `onwind_reference_level`，主值 disabled；gwa_reference = 候选 p_max_pu × 1 ÷（v5 / 参照），逐时上限 1；系数 1.281–1.973。只建开关与单元测试，不构建该变体。
- **最终网络（`645c37e9`）：** F1 2920 `88e3ced5…`、F2 2920 `5d84161a…`（D 盘 `builds/c2main`）；v5off 与 W14 逐值相同；静态检查与零松弛门全部通过；桥表更新（284 行）。
- **新发现：** PH_Luzon9 0 与 PH_Visayas10 0 两个节点不在 S4A 剖面节点表内。陆上风电 31.0 GW、光伏 15.8 GW 一直保留作者原曲线（L-C25），待审阅端决定。
- **测试：** 全量测试（HEAD `645c37e9`，`logs/ut_full_v5_C2.txt`）1 failed / 927 passed / 55 skipped / 5 deselected，1,905.89 s；唯一失败 `test_s1_built_networks::test_static_validation_passes_on_reload` 同基线；+8 passed 为 C 段新增测试。
- **56 时段回归（Gurobi 2 次，串行）：** F1 optimal 398,392,537,354.3792 EUR（相对 v4 D2c +35.202 bn / +9.69 %，相对 B 段 +2.218 bn），567 s，峰值 6.66 GiB；F2 optimal 412,955,722,810.13727 EUR（+36.812 bn / +9.79 %，相对 B 段 +2.445 bn），407 s，峰值 6.05 GiB（高于估计 5,898 MiB 约 5 %，仍在 Q18 门槛内）。V6 两次 ACCEPTED_LAYER2，停止分类 accepted；V5 旧门失败集 A1_A2、A1_A2_S4B、A3、B1、B8（B3 这次通过）。Owen 前提、恒等式、燃料舱检查通过，分摊全部为正；受益符号相对 v4 只有 LA 改变（− → +），B 段 ID 的负号消失，PH 三套都为负。只是冒烟，不作数量结论。
- **环境一致性：** Windows miniconda3 是用户按审阅端建议卸载的。本会话 Windows Python 命令清单与 WSL 重跑比对见 REPORT §8 第 11 条：W2–W7 一致，W1 只有一行 GBK 乱码；NGCP 页码由审阅端在项目环境之外复核。今后脚本只在 WSL 项目环境运行。
- **交付：** `REPORT.md` §12（SHA256 `9882dd2a…`）、`LIMITATIONS_V5.md`（新增 L-C23–L-C28）、`evidence/C1_*`、`C2_*`、`*_C2.*`、`smoke56_c2/` 小文件；审阅包 `REVIEW_9882dd2a.zip`（含 B、C 两段回归的不含许可证内容的小文件，不含网络；包的 SHA256 见 `REVIEW_ZIP_SHA256.txt`）；提交号与推送结果见 `PROGRESS.md` 最后一行。未建 PR（独立审查后再建），`cache/v4solved` 保留。等待审阅端审阅。
