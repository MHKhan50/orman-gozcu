"""Temporal hold-out, regional transfer and threshold trade-offs."""
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import __version__
from .dataset import TEST_YEARS, TRAIN_YEARS, VAL_YEARS, split
from .grid import REGIONS
from .metrics import at_threshold, report, threshold_for_recall
from .models import MODELS, Calibrated

SEEDS = (0, 1, 2, 3, 4)
BLUE, YELLOW, RED, GREEN, GREY = "#1F4E9C", "#E3A800", "#C8102E", "#5FA65A", "#8a94a8"


def _seeds(name):
    return SEEDS if name == "gbm" else (0,)


def temporal(df):
    train, val, test = split(df)
    rows, thresholds, per_year = [], [], []
    n_days = test["date"].nunique()
    for name in MODELS:
        for seed in _seeds(name):
            m = Calibrated(name, seed).fit(train, val)
            p = m.predict(test)
            rows.append({"model": name, "seed": seed, **report(test, p)})
            t = threshold_for_recall(val["label"].to_numpy(int), m.predict(val), 0.6)
            thresholds.append({"model": name, "seed": seed,
                               **at_threshold(test["label"].to_numpy(int), p, t, n_days)})
            for y in TEST_YEARS:
                mask = (test["year"] == y).to_numpy()
                r = report(test[mask], p[mask])
                per_year.append({"model": name, "seed": seed, "year": y,
                                 "average_precision": r["average_precision"], "base_rate": r["base_rate"]})
    return pd.DataFrame(rows), pd.DataFrame(thresholds), pd.DataFrame(per_year)


def transfer(df):
    """Train on two regions, test on the third, against a model trained on all three."""
    train, val, test = split(df)
    rows = []
    for region, _, _ in REGIONS:
        held = test[test["region"] == region]
        if held["label"].sum() == 0:
            continue
        for name in ("climatology", "logistic", "gbm"):
            for seed in _seeds(name):
                pooled = Calibrated(name, seed).fit(train, val).predict(held)
                other = Calibrated(name, seed).fit(train[train["region"] != region],
                                                   val[val["region"] != region]).predict(held)
                for setting, p in (("trained on all regions", pooled), ("region held out", other)):
                    rows.append({"region": region, "model": name, "seed": seed, "setting": setting,
                                 **report(held, p)})
    return pd.DataFrame(rows)


def summarise(frame, keys, cols):
    g = frame.groupby(keys)[cols]
    out = g.mean().add_suffix("_mean").join(g.std(ddof=1).fillna(0).add_suffix("_sd"))
    return out.reset_index()


def chart(summary, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = {"climatology": "Historical frequency", "persistence": "Fire today", "logistic": "Logistic regression",
             "gbm": "Gradient boosting"}
    colours = {"climatology": GREY, "persistence": YELLOW, "logistic": GREEN, "gbm": BLUE}
    s = summary.set_index("model").loc[list(MODELS)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, metric, title in ((axes[0], "average_precision", "Average precision (higher is better)"),
                              (axes[1], "top10_capture", "Next-day fire cells in each day's top 10%")):
        vals = s[metric + "_mean"].to_numpy()
        bars = ax.barh([names[m] for m in s.index], vals, xerr=s[metric + "_sd"].to_numpy(),
                       color=[colours[m] for m in s.index], capsize=3)
        ax.bar_label(bars, fmt="%.3f", padding=4, fontsize=9)
        ax.set_xlim(0, min(1.0, vals.max() * 1.3))
        ax.set_title(title, loc="left", fontsize=10)
        ax.invert_yaxis()
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle("Next-day fire risk, Türkiye, test seasons %d-%d" % (TEST_YEARS[0], TEST_YEARS[-1]),
                 x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def run(df, out_dir="results", data_info=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    metrics, thresholds, per_year = temporal(df)
    tr = transfer(df)
    cols = ["average_precision", "roc_auc", "brier", "ece", "top10_capture", "base_rate"]
    s_metrics = summarise(metrics, ["model"], cols)
    s_thr = summarise(thresholds, ["model"], ["threshold", "recall", "precision", "false_alarms_per_day",
                                              "missed_per_day"])
    s_year = summarise(per_year, ["model", "year"], ["average_precision", "base_rate"])
    s_tr = summarise(tr, ["region", "model", "setting"], ["average_precision", "roc_auc", "brier", "base_rate"])
    for name, frame in (("metrics_by_seed", metrics), ("metrics", s_metrics), ("thresholds", s_thr),
                        ("by_year", s_year), ("transfer", s_tr)):
        frame.to_csv(out / ("%s.csv" % name), index=False)
    chart(s_metrics, out / "next_day_risk.png")
    train, val, test = split(df)
    meta = {"project": "OrmanGözcü", "version": __version__, "cells": int(df["cell"].nunique()),
            "train_years": list(TRAIN_YEARS), "val_years": list(VAL_YEARS), "test_years": list(TEST_YEARS),
            "rows": {"train": len(train), "val": len(val), "test": len(test)},
            "positives": {"train": int(train["label"].sum()), "val": int(val["label"].sum()),
                          "test": int(test["label"].sum())},
            "gbm_seeds": list(SEEDS), "data": data_info, "python": sys.version.split()[0],
            "platform": platform.platform()}
    (out / "run_metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (out / "tables.md").write_text(tables(s_metrics, s_thr, s_year, s_tr, meta), encoding="utf-8")
    return s_metrics


def tables(s_metrics, s_thr, s_year, s_tr, meta):
    f = lambda m, sd: "%.3f ± %.3f" % (m, sd)  # noqa: E731
    L = ["# OrmanGözcü results", "",
         "%d cells, test seasons %s, %d test cell-days, %d with a next-day detection." % (
             meta["cells"], "-".join(map(str, (meta["test_years"][0], meta["test_years"][-1]))),
             meta["rows"]["test"], meta["positives"]["test"]), "",
         "## Test seasons, all regions", "",
         "| Model | Average precision | ROC AUC | Brier | ECE | Top-10% capture |", "|---|---|---|---|---|---|"]
    for _, r in s_metrics.iterrows():
        L.append("| %s | %s | %s | %s | %s | %s |" % (r["model"], f(r.average_precision_mean, r.average_precision_sd),
                 f(r.roc_auc_mean, r.roc_auc_sd), f(r.brier_mean, r.brier_sd), f(r.ece_mean, r.ece_sd),
                 f(r.top10_capture_mean, r.top10_capture_sd)))
    L += ["", "## Threshold chosen on 2020 for 60% recall, applied to the test seasons", "",
          "| Model | Recall | Precision | False alarms per day | Missed fire cells per day |", "|---|---|---|---|---|"]
    for _, r in s_thr.iterrows():
        L.append("| %s | %.3f | %.3f | %.1f | %.2f |" % (r["model"], r.recall_mean, r.precision_mean,
                 r.false_alarms_per_day_mean, r.missed_per_day_mean))
    L += ["", "## Average precision by test year", "", "| Model | Year | Average precision | Base rate |",
          "|---|---|---|---|"]
    for _, r in s_year.iterrows():
        L.append("| %s | %d | %.3f | %.4f |" % (r["model"], r.year, r.average_precision_mean, r.base_rate_mean))
    L += ["", "## Regional transfer (test seasons, held-out region only)", "",
          "| Region | Model | Setting | Average precision | ROC AUC | Brier |", "|---|---|---|---|---|---|"]
    for _, r in s_tr.iterrows():
        L.append("| %s | %s | %s | %.3f | %.3f | %.4f |" % (r["region"], r["model"], r["setting"],
                 r.average_precision_mean, r.roc_auc_mean, r.brier_mean))
    L += ["", "± is the standard deviation over gradient-boosting seeds; other models are deterministic.", ""]
    return "\n".join(L)
