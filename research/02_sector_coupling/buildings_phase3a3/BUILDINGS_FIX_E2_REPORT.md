# E2 — Prevent silent loss of positive annual heat

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Mode: validate; Version: Phase3A3-1; Date: 2026-10-01 Asia/Shanghai
- Verification Status: VERIFIED for the specified synthetic regressions; scientific inputs UNVERIFIED, human acceptance PENDING

## 结论与实现

**修复前失败 → 修复后通过。** 独立源码提交 `31037d60d69fa762c9ed8ec9ce8289d95bd6a181`；本轮测试提交 `1f9405720a873918614df5aad361580cff7cedde`；分支 `codex/buildings-e2`。源码基于冻结 U，未合并 R。

原 `prepare_heat_data` 将正年度量乘以 zero-HDD 曲线的 0/0 归一化，得到 NaN；`add_heat` 的 `.fillna(0)` 随后使需求消失。候选添加 `normalize_heat_profile`：正年度需求必须有有限、非负、正和的形状，否则 **raise ValueError**；零年度量允许输出零。网络消费端拒绝 NaN、inf、负 heat profile，删除此处静默置零。未创造替代曲线、未判断真实地区是否应该采暖。

## 完整丢量路径证据

测试实际串接目标版本的 producer 和 consumer。以 BN 合成例为例，R/S 各有 6,000,000 MWh space 和 2,000,000 MWh water，合计 16,000,000 MWh。zero-HDD 时原链最终只建立 4,000,000 MWh water，12,000,000 MWh space 被丢弃。另 10 国使用各自明确的合成年度目标，均有对应记录。

修复后 producer 抛错，**没有输出一个伪称守恒的零需求网络**；源年度身份保留在输入/诊断中。对无效曲线，正确结果是阻止构网，不是“成功生成了守恒的缺失曲线”。有效曲线才检验积分守恒。

## 验证范围与结果

- 11 国、每国 2 节点，72 个逐时点，跨 weekday/weekend、本地时区映射；合成形状非平坦。
- positive+zero/NaN/negative/inf shape：必须拒绝；negative annual：必须拒绝。
- zero annual+zero HDD：space 为零且独立 water 不丢；positive+valid shape：各国两部门、space/water 分别守恒。
- 显式按 3 小时均值聚合后乘 3 小时权重，重新验证积分。
- imported CSV profile 含 NaN/negative/inf：消费端拒绝。

| 检查 | U 修复前 | E2 修复后 |
|---|---:|---:|
| 断言数 | 417 | 197 |
| 失败数 | 43 | 0 |
| 有效输出最大年度能量误差，MWh | — | 1.862645149230957e−9 |

行数差异源于修复后的提前 raise：无效场景不再生成后续数量断言。矩阵以修复后定义的 197 项行为/守恒检查为基准；完整修复前记录仍保留。错误场景使用 `RAISE`/布尔行为结果，误差留空，不把空值伪装成 0。

数值阈值与 E1 一致：`1e−6 MWh + 1e−12 × abs(expected)`。所有有效场景均通过。证据：[前](evidence/E2_before.json)、[后](evidence/E2_after.json)、[矩阵](BUILDINGS_FIX_TEST_MATRIX.csv)、[源码补丁](patches/E2.patch)、[测试补丁](patches/E2_validation.patch)。

## 剩余限制

建议人工审查后独立合并。此补丁解决给定正年度量的 profile 丢量，不覆盖所有数据验证：上游年度表到节点表仍有 `.fillna(0.0)`，因此“年度量本身缺失”仍是数据门槛，不能宣称全部缺失处理已修复。现有准备脚本按逐小时归一化；3h 检验为显式积分验证，不是全年多分辨率工作流复现。需要合适 shape 的地区仍将正确停下等待证据。
