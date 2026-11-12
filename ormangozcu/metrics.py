import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def ece(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    total = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            total += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(total)


def top_share_capture(df, p, share=0.1):
    """Share of next-day fire cells that fall in each day's top `share` of cells by predicted risk."""
    d = pd.DataFrame({"date": df["date"].to_numpy(), "y": df["label"].to_numpy(), "p": p})
    caught = total = 0
    for _, g in d.groupby("date"):
        if g["y"].sum() == 0:
            continue
        k = max(1, int(round(share * len(g))))
        top = g.sort_values("p", ascending=False, kind="mergesort").head(k)
        caught += int(top["y"].sum())
        total += int(g["y"].sum())
    return caught / total if total else float("nan")


def threshold_for_recall(y, p, target=0.6):
    """Highest threshold whose recall on these rows is at least `target`."""
    order = np.sort(np.unique(p))[::-1]
    pos = y.sum()
    for t in order:
        if ((p >= t) & (y == 1)).sum() >= target * pos:
            return float(t)
    return float(order[-1])


def at_threshold(y, p, t, n_days):
    alarm = p >= t
    tp = int((alarm & (y == 1)).sum())
    fp = int((alarm & (y == 0)).sum())
    fn = int((~alarm & (y == 1)).sum())
    return {"threshold": t, "recall": tp / (tp + fn) if tp + fn else float("nan"),
            "precision": tp / (tp + fp) if tp + fp else float("nan"),
            "false_alarms_per_day": fp / n_days, "missed_per_day": fn / n_days}


def report(df, p):
    y = df["label"].to_numpy(int)
    return {"average_precision": float(average_precision_score(y, p)),
            "roc_auc": float(roc_auc_score(y, p)) if 0 < y.mean() < 1 else float("nan"),
            "brier": float(brier_score_loss(y, p)), "ece": ece(y, p),
            "top10_capture": top_share_capture(df, p, 0.1), "base_rate": float(y.mean())}
