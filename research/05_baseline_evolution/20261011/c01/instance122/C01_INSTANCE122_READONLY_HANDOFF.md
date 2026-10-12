# C-01：122号机迁移后的只读交接

2026-10-12。科学结论仍为 **C01_REPRESENTATION_DECISION_REQUIRED**。122号机当前文件身份为 **AWAITING_USER_JUPYTER_READONLY_RECEIPT**，不是已完成云端执行。

## 已完成且可直接复用

已对照固定Git提交 `efb0ddb5b66c0305715d285c9d622ed65228b728` 核对原C-01轻量证据的大小与SHA，并复核原ZIP的成员SHA及CRC。Scheme A仍引用PR #4提交 `8883de6fb3e15767c632ac92f535e8a423e90b69` 和Manifest SHA `a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720`；原件和旧ZIP保留，没有合并科学分支。

| 已真实核算的对象 | 原C-01结果，本轮复用 |
|---|---|
| 动态属性 | 1737条Load.p_set、460条Generator.p_max_pu、40条StorageUnit.inflow；2920三小时时段，无C00遗漏的其他动态表 |
| 96条时变电Load | 1条年度精确相等，52条正漂移、43条负漂移；其余1641条平坦Load精确相等 |
| 年度最大绝对表示差 | `159/137438953472 = 1.1568772606551647e-9 MWh`；很小但不等于精确零 |
| CF / 入流 | 460/460及40/40满足累计半ULP表示界；6条CF共44个原值高于1一个ULP，未裁剪 |
| Scheme A | 385组年度需求精确保持、385组满足D≤Q′；807账户未改也未重新派生 |
| 协议决定 | 日Load年度硬门槛未通过；双字表示候选仍PROPOSED_NOT_APPLIED，未获实施授权 |

具体逐资产Fraction、SHA、原值范围、ULP和方法均在 [原C-01主报告](../C01_DAILY_REPRESENTATION_PREFLIGHT.md) 与 `../evidence/` 中。本轮没有重复积分时序、扫描CSC或创建日输入。相同NetCDF字节加同一Scheme A配方足以复用确定性的精确有理数计算；机器迁移不会改变这个数学结论。

## 122号机尚未核实的事项

12核、约90GiB、磁盘约30GB余量、Python导入成功和许可证权限600均来自用户陈述。本轮没有连接或控制122，也没有读取许可证。WLS不影响本次NetCDF/Fraction表示审计，不增加许可证审批或求解准备任务。

历史云端NetCDF路径由首次Gate6快照的 `frozen_network` 引用获得，SHA为 `238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d`。该路径迁移后是否仍存在、内部符号链接是否有效，等待用户在Jupyter执行下列入口。没有将“SGP目录已迁移”当作逐文件身份通过。

Scheme A在本地固定Git对象中再次核实，**未确认它已部署到122**；旧NetCDF本身仍含旧Q。本轮只引用其未变时序并用独立Scheme A证据核年度关系，不把旧网络称为Scheme A新网络。身份脚本支持对已存在Scheme A目录进行可选四文件SHA核对；不寻找、上传或生成配方。

## 一个最小只读入口

将同包 `c01_122_readonly_identity.py` 手动上传至Jupyter的 `/root/autodl-tmp/SGP/`。它仅读一个指定NetCDF并枚举元数据，SHA通过后复用已完成核算；不重新执行全量聚合。不会导入PyPSA/Gurobi、访问许可证、运行shell、连接网络、启动旧入口或触碰历史Run。默认最多120秒，SHA分块4MiB，无大表或矩阵复制；唯一写入是 `c01_readonly_receipts/` 下独立时间戳JSON，禁止覆盖。

终端只需执行：

```bash
/root/autodl-tmp/SGP/env/gate5/bin/python3.11 -B /root/autodl-tmp/SGP/c01_122_readonly_identity.py
```

默认源文件：
`/root/autodl-tmp/SGP/worktrees/gate6_capture_20261008T200734Z/results_project/assembly_v1/research_fullsc_2050_assembly_v1_unsolved.nc`

若Jupyter显示该文件实际位于其他SGP内部路径，可显式加 `--network '<真实完整路径>'`，SHA、固定文件名与大小检查不变。脚本不递归搜索。若需要同时确认已存在的Scheme A文件，附加 `--scheme-a-directory '<已有配方目录>'`；不填写时明确记录 `NOT_CHECKED_NO_DIRECTORY_SUPPLIED`，不会假装新Q已上云。

预期终端返回新JSON的完整路径及SHA。请下载**该JSON**交回；不需要下载NetCDF或原时序。SHA不符、越界/悬空/循环链接、动态属性变化、时间形状不符、超时均停止并保存阻断状态；不修正、重试或退回旧快照。成功仅表示迁移文件可关联原C-01证据，科学结论仍为DECISION_REQUIRED，绝不是日模型GO。

## 已验证范围与下一步

本地验证新入口的普通文件/内部链接、SHA与大小拒绝、越界/悬空/循环拒绝、未知动态属性/形状/dtype拒绝和固定超时处理，使用合成字节文件及元数据对象；另只读打开本地冻结NetCDF的头部元数据验证真实读取接口，不读取时序表、不重新积分。具体数量和脚本SHA见 `C01_122_LOCAL_VALIDATION.json`。**这不是122的执行回执**。

收到122身份JSON后只需登记其实际结果，不必再跑原Fraction审计。若输入一致，继续由用户和ChatGPT决定如何处理95条电Load的精确表示差；若身份不同，报告差异并保持BLOCKED，不分析未经批准的新输入。Scheme A、Load、V3/V4/P2、历史消费标记及G6-05暂停状态均未改。没有日网络/LP构建或任何求解，交付后停止。
