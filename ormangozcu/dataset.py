"""Turn daily cell detections and weather into a next-day prediction table.

One row per (cell, day t) in the fire season. Features use day t and earlier only;
the label is whether the cell has at least one detection on day t+1.
"""
import datetime as dt

import numpy as np
import pandas as pd

from .grid import neighbours, region, weather_block

TRAIN_YEARS = (2016, 2017, 2018, 2019)
VAL_YEARS = (2020,)
TEST_YEARS = (2021, 2022, 2023, 2024)
MIN_TRAIN_FIRE_DAYS = 3
SEASON = ((5, 1), (10, 30))  # last feature day; its label is 31 October

FEATURES = ["fire_today", "log_count_today", "fire_days_7", "neighbour_fire_days_7", "hist_freq",
            "tmax", "precip", "wind_max", "et0", "precip_7", "precip_30", "dry_days", "et0_7",
            "doy_sin", "doy_cos"]


def fire_prone_cells(counts, years=TRAIN_YEARS, min_days=MIN_TRAIN_FIRE_DAYS):
    """Cells with enough fire days in the training years only, so the cell set leaks nothing from test years."""
    days = {}
    for (date, cell) in counts:
        if int(date[:4]) in years:
            days[cell] = days.get(cell, 0) + 1
    return sorted(c for c, n in days.items() if n >= min_days)


def _daily_frame(counts, weather, cells, years):
    dates = []
    for y in years:
        d, last = dt.date(y, 4, 1), dt.date(y, 10, 31)
        while d <= last:
            dates.append(d.isoformat())
            d += dt.timedelta(days=1)
    idx = pd.MultiIndex.from_product([cells, dates], names=["cell", "date"])
    df = pd.DataFrame(index=idx).reset_index()
    df["count"] = [counts.get((d, c), 0) for c, d in zip(df["cell"], df["date"])]
    for var, col in (("temperature_2m_max", "tmax"), ("precipitation_sum", "precip"),
                     ("wind_speed_10m_max", "wind_max"), ("et0_fao_evapotranspiration", "et0")):
        df[col] = [weather.get((d, weather_block(c)), {}).get(var, np.nan) for c, d in zip(df["cell"], df["date"])]
    df["year"] = df["date"].str[:4].astype(int)
    return df


def build(counts, weather, cells, years):
    df = _daily_frame(counts, weather, cells, years)
    df["fire"] = (df["count"] > 0).astype(int)
    df = df.sort_values(["cell", "date"]).reset_index(drop=True)
    g = df.groupby(["cell", "year"], sort=False)
    df["fire_today"] = df["fire"]
    df["log_count_today"] = np.log1p(df["count"])
    df["fire_days_7"] = g["fire"].transform(lambda s: s.rolling(7, min_periods=1).sum())
    df["precip_7"] = g["precip"].transform(lambda s: s.rolling(7, min_periods=1).sum())
    df["precip_30"] = g["precip"].transform(lambda s: s.rolling(30, min_periods=1).sum())
    df["et0_7"] = g["et0"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    def dry(s):
        out, run = [], 30
        for v in s:
            run = 0 if (v is not None and not np.isnan(v) and v >= 1.0) else min(run + 1, 30)
            out.append(run)
        return pd.Series(out, index=s.index)
    df["dry_days"] = g["precip"].transform(dry)
    df["label"] = g["fire"].shift(-1)

    lookup = df.set_index(["cell", "date"])["fire_days_7"].to_dict()
    df["neighbour_fire_days_7"] = [sum(lookup.get((n, d), 0) for n in neighbours(c))
                                   for c, d in zip(df["cell"], df["date"])]
    doy = pd.to_datetime(df["date"]).dt.dayofyear
    df["doy_sin"], df["doy_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    df["month"] = df["date"].str[5:7].astype(int)
    df["region"] = [region(c) for c in df["cell"]]

    lo, hi = "%02d-%02d" % SEASON[0], "%02d-%02d" % SEASON[1]
    md = df["date"].str[5:]
    df = df[(md >= lo) & (md <= hi) & df["label"].notna()].copy()
    df["label"] = df["label"].astype(int)
    return df


def add_history(df, train_years=TRAIN_YEARS):
    """Per-cell, per-month fire-day rate from the training years (the climatology baseline)."""
    train = df[df["year"].isin(train_years)]
    rate = train.groupby(["cell", "month"])["fire"].mean().rename("hist_freq")
    out = df.join(rate, on=["cell", "month"])
    out["hist_freq"] = out["hist_freq"].fillna(train["fire"].mean())
    return out


def split(df):
    return (df[df["year"].isin(TRAIN_YEARS)], df[df["year"].isin(VAL_YEARS)], df[df["year"].isin(TEST_YEARS)])
