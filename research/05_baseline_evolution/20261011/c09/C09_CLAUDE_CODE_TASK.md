# C09 执行任务（交给本机 Claude Code）

**授权范围：** 用户已同意 C09 方案（a），即精确分解后对主 LP 做一次求解。本任务**最多调用 1 次优化**，不重试，不改变任何参数。`start` 必须由用户本人确认后才能执行。

## 步骤

1. 进入 `work/c09_exact_decomposition_20261013/`，阅读 `C09_EXECUTION_GUIDE.md` 和 `RELEASE_DELIVERY.json`。
2. 核对本地 `C09_RELEASE.tar.gz` 的 SHA256，应为 `79d27d4f4c8b7e74a6e14621032ac39605e1c495f4dad8031a68830197d409e6`。
3. 执行 `python c09_control.py deploy`，等待输出 `C09_RELEASE_SHA_VERIFIED`。这一步求解调用为 0。
4. **先停下来**，把准入回执（主机、资源、许可证路径绑定）摘要给用户，请用户明确回复"开始"。
5. 收到用户确认后，执行 `python c09_control.py start`，只执行一次。若命令失败或结果不明确，不得重试，直接报告。
6. 每隔 2 至 3 分钟执行一次 `python c09_control.py observe`，直到快照中出现 `archive`（云端封存完成）。监控期间不向云端发送任何其他命令。
7. 执行 `python c09_control.py fetch`，核对 SHA256 后把归档解压到 `outputs/c09_daily_diagnostic/<run_id>/cloud_run/`。

## 汇报方式

按 `C09_EXECUTION_GUIDE.md` 中的 R1 至 R5 判定，写出 `C09_RESULT.md`，内容包括：
- Status、SolCount、Barrier 与 Simplex 迭代次数、Runtime；
- 全部 V4 门槛的结果；
- 与 C07A、C07B 的对照表；
- 资源占用与备份状态。

然后更新台账条目，打包 `C09_EXACT_DECOMPOSITION_REVIEW.zip`（含 SHA 与 CRC 清单）。在独立分支提交并推送，关联 PR #17，返回真实的 commit 和 PR 链接。

完成后停止，等待用户审阅。
