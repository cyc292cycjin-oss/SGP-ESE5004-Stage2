"""D 阶段状态文件写入工具（只读本地快照，不连云端）。

python d_status_writer.py loop <seconds> <max_rounds>   # 监控期间定时根据最新 D5 快照覆盖写 D_STAGE_STATUS.md
python d_status_writer.py once "<当前步骤>" "<关键数字>" "<下一步>"   # 主要步骤完成后手动覆盖写
"""
import json, sys, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
W = Path(__file__).resolve().parents[1]; SGT = timezone(timedelta(hours=8))
now = lambda: datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')


def write(step, numbers, nxt):
    (W / 'D_STAGE_STATUS.md').write_text(f'''# D 阶段状态

- **更新时间：** {now()}
- **当前步骤：** {step}
- **关键数字：** {numbers}
- **下一步：** {nxt}

授权依据：`D_STAGE_DELEGATION.md`（自主推进，按 DR1–DR5 与 "DR3 下一轮规则" 判定）。D-5 唯一一次求解 run_id `d5_main2920_20261012T212658Z_0162bbf4`。
''', encoding='utf-8')


def from_snapshot():
    snaps = sorted((W / 'monitor_snapshots').glob('D5_*.json'))
    if not snaps: return
    v = json.loads(snaps[-1].read_text()); r = v['receipts']; ph = (r.get('PHASE.json') or {}).get('phase')
    tail = [x for x in ((v.get('log') or {}).get('tail') or []) if x.strip()][-2:]
    res = v.get('resource') or {}
    nums = (f"快照 {snaps[-1].stem[3:]}；阶段 {ph}；日志末行 {' | '.join(s.strip() for s in tail)}；"
            f"RSS {res.get('rss_bytes', 0)/2**30:.1f} GiB；系统盘剩余 {res.get('disk_free_bytes', 0)/2**30:.1f} GiB；"
            f"错误/停止 {[k for k in r if 'FAILURE' in k or 'STOP' in k or 'ERROR' in k]}；封存 {'已完成' if v.get('_ARCHIVE_RECEIPT.json') else '未完成'}")
    write('D-5 唯一一次求解监控中（Crossover 清理阶段；不干预）', nums,
          '求解结束并云端封存后：fetch → SHA 核对 → 解压 → 本地复核 V4 → 按 DR1–DR5 判定；若 DR3 按"下一轮规则"计算 Dual Inf. 趋势')


if __name__ == '__main__':
    if sys.argv[1] == 'once': write(*sys.argv[2:5])
    else:
        sec, rounds = int(sys.argv[2]), int(sys.argv[3])
        for _ in range(rounds):
            if (W / 'D_STATUS_LOOP_STOP').exists(): break
            from_snapshot(); time.sleep(sec)
