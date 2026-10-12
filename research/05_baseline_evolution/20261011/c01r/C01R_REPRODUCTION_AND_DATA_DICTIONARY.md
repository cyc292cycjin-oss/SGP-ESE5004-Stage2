# C01R复核方法与台账数据字典

## 原件和执行边界

本轮复核源为Windows D工作区的冻结NetCDF及本地WSL仓库中指定Git对象。无需云端数据或许可证。脚本不导入PyPSA/Gurobi，不读取CSC/解向量，不构建网络或LP，不写原时序。只有`c01r/evidence`中新审计文件写入，使用exclusive-create，已存在则报错而非覆盖。

`verification/build_ledger.py`是本轮生成方法：Git/文件SHA→真实动态元数据→源列SHA→Fraction日均→最近binary64→精确相邻距离→逐资产A/B/C→Scheme A四字段/385组→台账。`verification/verify_independent.py`是独立复核方法：从源文件重新读取→共同二进制分母整数和→整数有效位舍入→逐日逐资产对照→Scheme A重新读取→汇总重建。两者不共享算术函数或导入彼此。

当前原件和结果已经验证，不为存储迁移重复执行。若审阅者需复核，可在独立副本/新输出目录中运行方法；需拥有清单内本地原NetCDF和固定Git对象。现有脚本的路径常量明确指向D工作区、已核WSL仓库和本轮审计输出，不能直接当云端部署/运行入口。保留现有回执，不删文件绕过exclusive-create。不得将这些脚本扩展为模型或求解入口。

## 台账结构

- `source_identity`：未求解源装配版本/SourceRun标识、原NetCDF/Load表SHA、科学Git及Scheme A/C01身份。不是把源版本冒充已运行的Scheme A网络。
- `day_buckets`：365个日索引、日期、对应2920源索引的8项列表、24h权重；每条Load引用同一全量桶映射。
- `records`：1737条资产。`DemandOwner`来自冻结registry InputID及Country/Sector/Account/Carrier/Year交叉表；是审计归属字段，不是声称NetCDF已有同名原生属性。来源列与InputID明确保存。
- `daily_records`：96时变电Load各365行；列名在`daily_record_columns`。依次为日索引、精确均值MW、最终binary64 hex MW、带符号误差MW、精确半ULP界MW、中点标记、A_PASS。没有原2920大时序或生产日输入文件。
- `daily_records_RLE`：1641平坦Load每条一条0…364完整日范围记录；全部原值逐位恒定已核，等价表达每天原值/零误差，不省略任何日桶。
- 年度字段：`E_original_MWh`是科学权威年量；`E_daily_MWh`是审计模拟的实装量；`DeltaE_MWh`、绝对值、相对值、半ULP年度界及指定十进制精确阈值均保存为约分有理数字符串，不是浮点判定。
- `checks`：A/B/C绝对/C相对及平坦身份分别列出；`AND_pass`由所有适用条件相与。非适用字段明确NOT_APPLICABLE，不能把字符串真值当计算门槛；实际代码对适用类别分支处理。
- `Scheme_A_groups`：385组逐组原D、日D、Q′、精确余量和807账户ID。只复算关系，不写入Q。D≤Q′不被误记为D=Q′。
- `summary`：精确/正/负数量、有符号和、绝对和、最大绝对/相对及阻断数；每资产独立通过后才生成。全表SHA在独立回执/冻结清单中，避免自哈希递归。

半ULP不是普通`math.ulp(rounded)/2`的边界猜测：对于不精确均值，用实际夹住它的两个相邻binary64之间距离的一半；精确表示时取左右相邻距离较小者/2（误差为0）。独立验证覆盖binade和subnormal边界、中点偶数及拒绝条件。

审核JSON约7.2MB主要是35,040条日舍入证据，不包含完整原始时序、大NetCDF、CSC、X/Pi/RC或任何凭据。它不被任何组装程序消费，本轮未输出可直接组装的日输入NetCDF/NPY。

## 历史与未授权范围

原C00协议文件保持字节不变；本轮前GO/NO-GO清单另存history。原C01的严格相等失败及双字候选都保留为历史；本次正式选择有界binary64，未实施双字方案。V4原件SHA、Scheme A180项源修复、其他627账户及原始Load/Q/物理参数不改。

未开展任何C02/C03、AutoDL操作或G6-05诊断。未来生产日数据导出/回读、原生交接、科学验收必须另行授权；本台账通过不等于未来完整LP可行。
