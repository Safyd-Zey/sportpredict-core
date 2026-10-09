"""Reliability (calibration) diagram - the standard way to check that
predicted probabilities match observed frequencies (cf. Murphy & Winkler, 1977)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

_LABELS = {"p_home": ("Home win", 2), "p_draw": ("Draw", 1), "p_away": ("Away win", 0)}


def calibration_table(prob: np.ndarray, hit: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    """Mean predicted probability vs observed frequency in equal-width bins."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(prob, bins) - 1, 0, n_bins - 1)
    df = pd.DataFrame({"bin": idx, "prob": prob, "hit": hit.astype(float)})
    out = df.groupby("bin").agg(mean_pred=("prob", "mean"), freq=("hit", "mean"), n=("hit", "size"))
    return out.reset_index()


def reliability_diagram(predictions: pd.DataFrame, path: str | Path, n_bins: int = 10) -> Path:
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfectly calibrated")
    for col, (label, code) in _LABELS.items():
        tab = calibration_table(
            predictions[col].to_numpy(), (predictions["outcome"] == code).to_numpy(), n_bins
        )
        tab = tab[tab["n"] >= 20]
        ax.plot(tab["mean_pred"], tab["freq"], "o-", label=label)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Reliability diagram (test period)")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
