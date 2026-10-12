# C-02R到C-03衔接专项复核

日期：2026-10-12。依据：用户已上传的C02R_MINIMAL_CHECKER_REPAIR_REVIEW.zip、父C02_DAILY_BUILD_STATIC_REVIEW.zip、C00_DAILY_365_PROTOCOL_C01R_V1.md和上一轮build-only指令。

## 结论

上一条指令不能使任务自动进入实际云端求解：它明确禁止任何优化，并在静态验收后停止。这不是求解器故障。
同时，现有交付尚缺日LP到原生求解/日V4的实际接口衔接。补上授权文字本身并不足够。
建议把检查器修复、一次构建、接口适配、WLS/原生回读、一次条件式优化、日V4和保全合并为一个执行任务；新求解授权须由用户明确确认/转发，不能继承旧build-only授权。

## 实际代码证据

1. `c02_launch.py:19–33`：claim和授权明确build_only/solver_calls_allowed=0，deadline为t0+1800；启动的是c02_supervise.py。不是求解启动器。
2. `c02_worker.py:31–36`：主动封锁OptimizationAccessor.__call__、solve_model、linopy.Model.solve以及to_gurobipy/to_highspy。
3. `c02_worker.py:47–59`：export_model后删除网络对象、生成make_binding和synthetic_tests、写出C02_BUILD_STATIC_ACCEPTED_NO_SOLVE；没有后续原生求解派发。
4. 候选`c02_model.py:129–142,233–269`：输出按行分块CSR，以及rows/columns/sense='min'/V3_offset元数据。
5. 旧`source/adapter.py:62–83,115–159`：要求num_col/num_row/sense=1/offset、每数组count和全局CSC start/index/value；不能不做格式与标签转换就读取当前C02产物。
6. `c02_binding.py:15–29`只生成身份绑定JSON；31–54执行合成V4测试。`DAILY_V4_BINDING_STATUS.json`为NOT_CREATED_BLOCKED_BEFORE_COMPLETE_LP_IDENTITY、usable_for_C03=false。
7. 旧`source/acceptance_pipeline.py`的postprocess_raw读取mapping目录下R.npy/D.npy/vlabels.npy/MAPPING_MANIFEST.json。新C02的LABELS.json、分块R和CSR必须与该实际读取接口衔接，不能只宣称阈值不变。
8. `c02_supervise.py:6–14`建模停止链为TERM后最多3秒升级KILL；它不是C00为原生求解约定的120秒/30秒收尾链。不得原样当求解监护器继续运行。
9. C00/C01R协议§6–8：日模型以第一次Gate6配置为基准（BarConvTol=1e-6、NumericFocus=0、FeasibilityTol=1e-6、DualReductions=1），原生TimeLimit拟定3600秒、整个运行9150秒。P2和暂停的G6-05不得混用。

## 补充的最小范围

- 已批准两类检查器修复；原科学输入、目标规则、V4阈值不变。
- 正式建模前准备日LP格式/标签/目标接口和完整返回向量验收路径，以合成无求解数据测试。
- 必须按实际新LP维数、列界/行界、原/V3成本、offset、D/R和原生回读验证。
- 构建进程维持no-solve保护；单独的C03 worker在成功回执和新增条件式授权齐备后才可优化。
- 复用已有完整静态合格产物，禁止并发/重复启动，不能清除旧claim或覆盖历史。
- 原生状态与原始向量先保存，后处理失败也不重新求解。

## 复核边界

本次完成压缩包CRC和清单文件SHA/大小验证，以及上述本地源码静态阅读。未连接AutoDL、未读取当前远端进程或许可证，未构建模型、未运行优化器。未独立验证当前GitHub远端状态。接口不兼容的判断针对随包给出的版本；如果Codex已生成更新的适配器，应以其实际提交及测试回执核实，不能重复开发。

## 清单核验

```json
{
  "C02_DAILY_BUILD_STATIC_REVIEW": {
    "files_checked": 78,
    "mismatches": []
  },
  "C02R_MINIMAL_CHECKER_REPAIR_REVIEW": {
    "files_checked": 30,
    "mismatches": []
  }
}
```

## 所读源码指纹

```json
[
  {
    "file": "C02R_MINIMAL_CHECKER_REPAIR_REVIEW/research/05_baseline_evolution/20261011/c02r/candidate/c02_model.py",
    "sha256": "fa8c3905dfc6bfd36b57cf7ceed8592b63dba7943d8d0c2babdee32f507e0f76"
  },
  {
    "file": "C02_DAILY_BUILD_STATIC_REVIEW/research/05_baseline_evolution/20261011/c02/code/c02_worker.py",
    "sha256": "8aedff9783d15c3d443705323ffbe00c9b7b5cd8e7a9ba4614ba1efd93d7b021"
  },
  {
    "file": "C02_DAILY_BUILD_STATIC_REVIEW/research/05_baseline_evolution/20261011/c02/code/c02_launch.py",
    "sha256": "51bec16c8de5e6fc2686fbf65a898db6a805679c5895b3bd984f987bd2f503dc"
  },
  {
    "file": "C02_DAILY_BUILD_STATIC_REVIEW/research/05_baseline_evolution/20261011/c02/code/c02_supervise.py",
    "sha256": "41f6fdbea33cf3ced122b3c11afc7bc6832cf8b068282e2a9dad3f86d19c3519"
  },
  {
    "file": "C02_DAILY_BUILD_STATIC_REVIEW/research/05_baseline_evolution/20261011/c02/code/c02_binding.py",
    "sha256": "8f432d12a6ea28785652cfee7a272ec6121c5a226443bff2016fe416ebed4e29"
  },
  {
    "file": "C02_DAILY_BUILD_STATIC_REVIEW/research/05_baseline_evolution/20261011/c02/code/source/adapter.py",
    "sha256": "b403a180badb9e3fdb1f0c73c47cc95fb6f9acf7b44068b595a65d125fd2a33e"
  },
  {
    "file": "C02_DAILY_BUILD_STATIC_REVIEW/research/05_baseline_evolution/20261011/c02/code/source/acceptance_pipeline.py",
    "sha256": "e5e9dd1568721774ca52482c1d42e87a848b5561cedfb0704679cc587cd68743"
  },
  {
    "file": "C02_DAILY_BUILD_STATIC_REVIEW/research/05_baseline_evolution/20261011/c02/DAILY_V4_BINDING_STATUS.json",
    "sha256": "62afc6304caffba8594b817bc55e5481718af78ee8306f628ec4c6a6deb0b7b9"
  }
]
```
