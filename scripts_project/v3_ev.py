"""V3 (decision 165; D165-1 a, D165-2, D165-3 a, D165-4): EV weekly shapes and node time zones.

    PYTHONHASHSEED=0 python scripts_project/v3_ev.py --ramp-dir <04_ev> --nodes <V2_NODES.csv> --id-tz <ID_NODE_TIMEZONE_PROPOSAL.csv>

RAMP-mobility (Euro-Calliope) hourly series 2013, 26 countries, labelled UTC, generated on the local clock with daylight saving: every country is converted to
its local clock, averaged by (weekday, hour), normalised to mean 1 (consumption) and averaged over the 26 countries = a 168-hour local-clock week. ev_series()
turns the week into a model series: the model snapshots are 2013 UTC, the local week of a node follows from its UTC offset (half hours by linear interpolation).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from d1_common import ROOT, sha256

SCRIPT = "scripts_project/v3_ev.py"
V3_DIR = ROOT / "research_inputs/transport_v3"
SHAPE = V3_DIR / "EV_WEEKLY_LOCAL_SHAPE_V3.csv"
NODE_TZ = V3_DIR / "EV_NODE_TIMEZONE_V3.csv"
TZ = dict(AUT="Vienna", BEL="Brussels", CHE="Zurich", CZE="Prague", DEU="Berlin", DNK="Copenhagen", ESP="Madrid", EST="Tallinn", FIN="Helsinki", FRA="Paris", GBR="London", HRV="Zagreb", HUN="Budapest",
          IRL="Dublin", ITA="Rome", LTU="Vilnius", LUX="Luxembourg", LVA="Riga", NLD="Amsterdam", NOR="Oslo", POL="Warsaw", PRT="Lisbon", ROU="Bucharest", SVK="Bratislava", SVN="Ljubljana", SWE="Stockholm")
COUNTRY_OFFSET = {"MM": 6.5, "TH": 7.0, "VN": 7.0, "KH": 7.0, "LA": 7.0, "MY": 8.0, "SG": 8.0, "PH": 8.0, "BN": 8.0, "TL": 9.0}   # decision 165; ID by node


def local_week(path: Path, col: str, normalise: bool, year: int = 2013) -> pd.Series:
    t = pd.read_csv(path, usecols=["datetime", "year", "country_code", col])
    t = t[t.year == year]; t["u"] = pd.to_datetime(t.datetime, utc=True)
    w = []
    for c, g in t.groupby("country_code"):
        loc = g.u.dt.tz_convert("Europe/" + TZ[c])
        s = pd.Series(g[col].to_numpy(), index=pd.MultiIndex.from_arrays([loc.dt.dayofweek.to_numpy(), loc.dt.hour.to_numpy()], names=["weekday", "hour"])).groupby(level=[0, 1]).mean()
        w.append(s / s.mean() if normalise else s)
    return pd.concat(w, axis=1).mean(axis=1)


def ev_series(snapshots: pd.DatetimeIndex, offset_h: float, week: np.ndarray, hours_per_snapshot: int = 3) -> np.ndarray:
    """Mean of the circular 168-hour local week over each model snapshot (model snapshots are UTC, Monday 00:00 = index 0 of week)."""
    idx = snapshots.dayofweek.to_numpy() * 24.0 + snapshots.hour.to_numpy() + offset_h
    out = np.zeros(len(snapshots))
    for h in range(hours_per_snapshot):
        x = (idx + h) % 168.0; i = np.floor(x).astype(int); f = x - i
        out += (1.0 - f) * week[i % 168] + f * week[(i + 1) % 168]
    return out / hours_per_snapshot


def main():
    p = argparse.ArgumentParser(); p.add_argument("--ramp-dir", type=Path, required=True); p.add_argument("--nodes", type=Path, required=True); p.add_argument("--id-tz", type=Path, required=True); a = p.parse_args()
    V3_DIR.mkdir(parents=True, exist_ok=True)
    fc, fp = a.ramp_dir / "ramp-ev-consumption-profiles.csv.gz", a.ramp_dir / "ramp-ev-plugin-profiles.csv.gz"
    c = local_week(fc, "demand", True); q = local_week(fp, "plugin", False)
    t = pd.DataFrame(dict(consumption_norm=c, plugin=q)).reset_index().sort_values(["weekday", "hour"])
    t["consumption_norm"] = t.consumption_norm / t.consumption_norm.mean()
    if len(t) != 168 or t.isna().any().any():
        raise ValueError("weekly shape incomplete")
    t.to_csv(SHAPE, index=False)
    n = pd.read_csv(a.nodes, index_col=0); n = n[n.carrier == "AC"]
    tz = pd.read_csv(a.id_tz, index_col=0)
    rows = [dict(node=k, country=z.country, utc_offset_h=(float(tz.at[k, "tz"]) if z.country == "ID" else COUNTRY_OFFSET[z.country]), basis=(f"province {tz.at[k, 'NAME_1']}" if z.country == "ID" else "country")) for k, z in n.iterrows()]
    pd.DataFrame(rows).to_csv(NODE_TZ, index=False)
    evid = dict(script=SCRIPT, year=2013, countries=len(TZ), inputs={f.name: sha256(f) for f in (fc, fp)}, shape_sha256=sha256(SHAPE), weekday_mean=t.groupby("weekday").consumption_norm.mean().round(4).to_dict(), peak_local_hour_weekday=int(t[t.weekday < 5].groupby("hour").consumption_norm.mean().idxmax()),
                diurnal_peak_over_mean=float(t.groupby("hour").consumption_norm.mean().max()), plugin_mean=float(t.plugin.mean()), plugin_min=float(t.plugin.min()), plugin_max=float(t.plugin.max()))
    (V3_DIR / "EV_V3_EVIDENCE.json").write_text(json.dumps(evid, indent=1, sort_keys=True) + "\n")
    print(json.dumps(evid, indent=0)[:900])
    print(pd.DataFrame(rows).groupby(["country", "utc_offset_h"]).size().to_dict())


if __name__ == "__main__":
    main()
