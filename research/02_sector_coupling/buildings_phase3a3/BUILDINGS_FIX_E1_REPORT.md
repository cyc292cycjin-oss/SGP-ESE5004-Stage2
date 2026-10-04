# E1 — Residential / Services heat conservation

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Mode: validate; Version: Phase3A3-1; Date: 2026-10-01 Asia/Shanghai
- Verification Status: VERIFIED for the specified synthetic regressions; scientific inputs UNVERIFIED, human acceptance PENDING

## 结论与实现

**修复前失败 → 修复后通过。** 沿用已独立实现的 E1，未重复改写上轮源码。源码提交 `92e9118be20f0b3802f385adac2f56650d57299d`；本轮增强测试提交 `59dbd34880bcdb367fed54cdee39a2ace40182fd`；分支 `codex/buildings-e1`。基线为 U `a3616a68ee44592af6527ca9024a90f1956646ae`。未合并 Research Model。

原实现把 R/S central heat 合成一个 Load，随后 Residential 的逐国回写覆盖了包括 Services 在内的 heat loads。候选补丁保留共享供热 Bus，但分别建立 R/S central Load；Residential 只按自身剩余热量比例缩放自己的 Load，删除覆盖全部 heat loads 的循环。成本、技术集合、原始年度输入及配置不变。源码 diff 为 29 行增加、41 行删除。

## 守恒定义

所有测试用量均为合成输入。令某国 Residential 原热量为 H，既有固定燃料相关部分为 F，则保留原混合边界的剩余热服务账户为 H−F。补丁不把 F 自动改造成有用热，也不宣称现有模型已实现“全部燃料参与内生供热竞争”。F=0 的测试单独验证完整指定热服务 H 的守恒。

对每个节点与部门，已知分配热服务 q、central 份额 d、loss 参数 l：

- distributed service = q(1−d)
- central service = qd
- central Load = qd(1+l)
- separately reported district loss = qdl

保留上游 **加成式** loss 约定；没有悄悄改成 qd/(1−l)。从 central Load 扣回 loss 后再核对年度服务量。测试中的 d/l 是夹具参数，未授予 ASEAN 科学适用性。外生 space reduction 测试只核对现有配置作用后的明确目标，不改变研究配置。

## 测试证据

11 国标识、每国 2 节点、异质年度量、不同 R/S/space/water 曲线、非均匀 snapshot 权重 [1,3,2,4,1,2] 小时。7 个场景：混合固定燃料、全部热服务、R=0、S=0、零 central 分配、最大测试 central potential、既有 space reduction 开关。分别验证各国 R/S 服务量、DH loss、Services 曲线未被改写、direct electricity 和固定油/气/生物质燃料量。

| 检查 | U 修复前 | E1 修复后 |
|---|---:|---:|
| 断言总数 | 777 | 777 |
| 失败数 | 308 | 0 |
| 最大年度能量绝对误差，MWh | 5,900,000 | 1.862645149230957e−9 |

显式判据：`abs(error) <= 1e-6 MWh + 1e-12 × abs(expected MWh)`。Services 逐时曲线不变使用精确零差判据。这里的 777 是断言数，不是独立样本或统计重复次数。

证据：[前结果](evidence/E1_before.json)、[后结果](evidence/E1_after.json)、[统一矩阵](BUILDINGS_FIX_TEST_MATRIX.csv)、[源码补丁](patches/E1.patch)、[测试补丁](patches/E1_validation.patch)。测试直接载入目标 SHA 的函数，使用真实 PyPSA Network，但输入适配器与成本是合成夹具，未执行完整 Snakemake/optimizer。

首轮扩展夹具遗漏了本环境需要显式赋值的 Bus.location，造成固定燃料 NaN；已修正夹具并保留[诊断记录](evidence/harness_diagnostics/README.txt)。没有把夹具失败归咎于模型，也没有用它计算最终通过率。

## 合并建议与限制

建议人工审查后独立合并源码提交及其测试提交。E1+E2+E4 的隔离源码组合回归通过。E1 不完成 final-fuel→useful-service 科学转换，不修复 E3，不决定 cooking、DH、existing stock 边界。其“after”指候选分支，不表示 Research Model 已修改。
