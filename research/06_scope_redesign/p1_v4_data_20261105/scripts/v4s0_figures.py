"""V4 S0 figures (static PNG for V4_DATA_SCOPE.md): fig1 industry 2050 bound total by v3 sub-sector per country; fig2 the six distinct FfE shapes over one week.

    python scripts/v4s0_figures.py --work <work dir>

Palette: reference categorical slots 1-6 (light mode), validated with the dataviz validator (all checks pass; three slots below 3:1 contrast ->
legend + direct labels + the tables in the report).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"


def font():
    for f in ("/mnt/c/Windows/Fonts/msyh.ttc", "/mnt/c/Windows/Fonts/simhei.ttf"):
        if Path(f).exists():
            font_manager.fontManager.addfont(f)
            return font_manager.FontProperties(fname=f).get_name()
    return None


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)


def fig1(work: Path):
    s = pd.read_csv(work / "evidence/V3_SUBSECTOR_2050_BY_COUNTRY.csv")
    s["group"] = s.subsector.where(~s.subsector.str.startswith("nonferrous"), "nonferrous")
    t = s.pivot_table(index="country", columns="group", values="twh_2050", aggfunc="sum").fillna(0.0)
    order = ["other", "dispersed", "steel", "cement", "ammonia", "nonferrous"]
    names = {"other": "其他（other）", "dispersed": "UNSD 分行回退（dispersed）", "steel": "钢铁", "cement": "水泥", "ammonia": "氨（产品）", "nonferrous": "有色（镍、铝、氧化铝、铜）"}
    t = t.reindex(columns=order, fill_value=0.0)
    t = t[t.sum(axis=1) > 0]
    tot = t.sum(axis=1); t = t.loc[tot.sort_values().index]; tot = tot.loc[t.index]
    sh = t.div(tot, axis=0) * 100
    fig, ax = plt.subplots(figsize=(9.5, 4.6), dpi=150); fig.patch.set_facecolor(SURFACE); style(ax)
    left = np.zeros(len(sh))
    for i, c in enumerate(order):
        ax.barh(range(len(sh)), sh[c], left=left, height=0.62, color=SLOTS[i], edgecolor=SURFACE, linewidth=1.5, label=names[c])
        for j, v in enumerate(sh[c]):
            if c in ("other", "dispersed") and v >= 12:
                ax.text(left[j] + v / 2, j, f"{v:.0f}%", ha="center", va="center", fontsize=8, color="#ffffff" if c == "other" else INK)
        left += sh[c].to_numpy()
    for j, (c, v) in enumerate(tot.items()):
        ax.text(101.5, j, f"{v:,.1f} TWh", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(range(len(sh))); ax.set_yticklabels(sh.index, color=INK)
    ax.set_xlim(0, 100); ax.set_xlabel("占本国 2050 年网络绑定工业总量的比例（%）", color=INK2, fontsize=9)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.set_title("v3 工业负荷结构（2050，网络绑定口径；东盟 11 国合计 3,820.1 TWh，TL 为 0）", loc="left", fontsize=10.5, color=INK)
    ax.legend(ncol=3, fontsize=8, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.13), labelcolor=INK)
    fig.subplots_adjust(left=0.06, right=0.88, top=0.90, bottom=0.27)
    fig.savefig(work / "evidence/fig1_v3_industry_structure_2050.png", facecolor=SURFACE); plt.close(fig)


def fig2(work: Path):
    d = json.loads((work / "downloads/08_ffe_profiles/opendata.customization").read_text(encoding="utf-8"))
    v = {int(r["internal_id"][0]): np.asarray(r["values"], dtype=float) for r in d["data"]}
    shapes = [(1, "钢铁 = 造纸"), (4, "非金属矿物"), (5, "运输设备 = 机械"), (7, "采矿"), (8, "食品"), (10, "木材 = 建筑 = 纺织 = 未细分")]
    start = 24 * 8   # 2017-01-09 (Monday) 00:00, one week
    fig, ax = plt.subplots(figsize=(9.5, 4.0), dpi=150); fig.patch.set_facecolor(SURFACE); style(ax)
    x = np.arange(168)
    for i, (k, lab) in enumerate(shapes):
        y = v[k][start:start + 168] / v[k].mean()
        ax.plot(x, y, color=SLOTS[i], linewidth=1.6, label=lab)
    ax.axhline(1.0, color=INK2, linewidth=0.6, linestyle=(0, (3, 3)))
    ax.set_xticks(np.arange(0, 169, 24)); ax.set_xticklabels(["周一", "周二", "周三", "周四", "周五", "周六", "周日", ""], color=INK)
    ax.set_xlim(0, 168); ax.set_ylabel("相对年均值（1 = 年均）", color=INK2, fontsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.set_title("FfE 数据集 59：6 种不同的归一化电负荷形状（2017-01-09 起一周，时区未注明）", loc="left", fontsize=10.5, color=INK)
    ax.legend(ncol=3, fontsize=8, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.10), labelcolor=INK)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.27)
    fig.savefig(work / "evidence/fig2_ffe_shapes_week.png", facecolor=SURFACE); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    f = font()
    if f:
        plt.rcParams["font.family"] = f
    plt.rcParams["axes.unicode_minus"] = False
    fig1(a.work); fig2(a.work)


if __name__ == "__main__":
    main()
