# 作者结果包只读审计

**结果包可获取；完成完整 ZIP 目录审计和两个网络成员的内容审计。下载/读取作者结果不是独立复现。**

来源：[results-asean-paper-v1.zip](https://drive.google.com/file/d/194my_d3eotQ1GvsGGN5KOZGWOHEivoQy/view)，由官方论文文档链接。Google Drive 返回下载确认页，文件过大无法扫描；仅作为数据读取，没有执行包内内容。

## 获取范围

归档总字节数 **9,935,957,438**；解压成员总大小 12,942,145,869 字节。通过 HTTP Range 读取 ZIP64 目录和选定成员，未下载整包。目录共 59 条：15 个目录、44 个 `.nc` 文件；没有独立 README、config YAML、日志、输入文件或 manifest。完整清单、CRC、压缩大小、偏移与 ZIP 时间字段见 `RESULTS_ZIP_DIRECTORY.json`。

| 目录 | 网络数 |
|---|---:|
| baseline-aims-3H / baseline-asean-3H / baseline-existing-3H | 各 6 |
| decarbonize-aims-3H / decarbonize-asean-3H / decarbonize-existing-3H | 各 6 |
| sensitivity-roof100-3H / roof200-3H / roof450-3H | 各 1 |
| sensitivity-1H / sensitivity-3H / sensitivity-6H | 各 1 |
| sensitivity-50n-3H / sensitivity-200n-3H | 各 1 |

六个主情景的文件名包含 2025、2030、2035、2040、2045、2050；敏感性为 2050。目录名称及时间戳是归档线索，不是运行成功的证明。论文整理配置中还列有 sensitivity-overnight-3H，而本包目录没有该同名情景，不能假设文件遗漏或与另一个敏感性等价。

## 两个已完整读取的成员

共同文件名格式为 `elec_s_100_ec_lv2.0__3h_<year>_0.071_DEC_0export.nc`。

| 成员 | 解压大小 | SHA256 |
|---|---:|---|
| baseline-aims-3H，2025 | 243,844,813 B | `06152be56ee41f64bfdca42fd24aeaf363ab61f931fec7b5e4bc12f6d6456ecb` |
| decarbonize-aims-3H，2050 | 348,035,096 B | `3ac28875630cffbf8b7f3b1e80dbc7eb293d36e7f62efd1578beec457d54d745` |

读取时 ZIP CRC 校验通过。成员保留在本目录 `cache/results-asean-paper-v1/`，大文件不提交 Git；`RESULTS_MEMBER_HASHES.json` 记录其可重取身份。**整包 SHA256 未计算**，其余 42 个网络也没有内容 SHA256；目录 CRC32 不能冒充加密哈希。分段请求审计见 `RESULTS_RANGE_LOG.json`、`RESULTS_MEMBER_RANGE_LOG.json`。

## metadata 与已保存结果

两者 `meta.git_commit` 均为 `5bacad702ccfed17ad19ab510fa710651e966f2c`，`network_pypsa_version=0.30.3`，`tutorial=false`；2920 个三小时快照，objective/generators/stores 权重各 8760。完整内嵌配置见 `effective_config/`；网络属性/组件分类见 `RESULTS_NETWORK_EVIDENCE.json`。

| 保存字段 | baseline 2025 | decarbonize 2050 |
|---|---:|---:|
| network_objective | 51,958,123,545.77296 | 94,026,128,588.01077 |
| network_objective_constant | 8,754,735,116.417757 | 9,897,267,130.891512 |
| CO2Limit | 无 | 100,000,000 tCO₂ |
| lv_limit | 353,746,853.52332264 | 353,746,853.52332264 |
| 工业电力 Load 加权量 | 721,064,894.9873369 MWh | 1,586,856,970.6237652 MWh |

这些是**作者已保存数值**，不是本项目新求解结果，不直接等于论文某表的指标。objective 与 objective_constant 的统计关系、跨年贴现及论文成本口径尚未逐项核对；不能从两行跨年结果估算互联收益。

工业需求为静态 `loads_p_set`，不能只检查 `loads_t_p_set`。本审计合并静态和时变 Load 后才报告上述非零值。这证明两个作者样本的工业电力需求并非当前教程的全零状态，但不证明原始 full-SC 工业数据已验收；final_adjustment 会重分配电力需求。

终态 Load 包括 AC、industry electricity、agriculture electricity、rail transport electricity、land transport EV。结合 `only_elec_network=true` 和论文范围，它是保留若干部门电力服务/技术结构的电力案例，不能据 sector 开关声称作者已验证完整非电需求。

保存的约束支持 baseline 与 decarbonized 的实现区别。结果包没有独立 solver log、完整输入哈希、环境锁及工作区 dirty 记录；不能把有 objective/dual 值等同于已独立验证 solver_status=optimal。进一步复现应使用本次恢复的作者版本及配置作为对照，而不是直接套用 2026-09 的 main。

`read_results_members.py` 只按固定名单读取两个成员；`inspect_results.py` 用 xarray 读取，不导入作者脚本或调用求解器。
