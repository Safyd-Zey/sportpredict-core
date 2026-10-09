"""Time-based backtesting: fit on the past, evaluate on the future."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from sportpredict.elo import EloConfig, compute_elo
from sportpredict.metrics import evaluate
from sportpredict.model import OrderedLogit


@dataclass
class BacktestResult:
    metrics: dict[str, dict[str, float]]
    predictions: pd.DataFrame
    params: dict[str, float] = field(default_factory=dict)


def backtest(
    matches: pd.DataFrame,
    train_start: str,
    test_start: str,
    cfg: EloConfig | None = None,
) -> BacktestResult:
    """Fit the ordered logit on [train_start, test_start) and score [test_start, end].

    Elo ratings are computed over the full history *sequentially*, so every
    test-set feature uses only matches played before that test match.
    """
    rated = compute_elo(matches, cfg)
    t0, t1 = pd.Timestamp(train_start), pd.Timestamp(test_start)
    if t0 >= t1:
        raise ValueError("train_start must be earlier than test_start")
    train = rated[(rated["date"] >= t0) & (rated["date"] < t1)]
    test = rated[rated["date"] >= t1]
    if train.empty or test.empty:
        raise ValueError("empty train or test period")

    y_test = test["outcome"].to_numpy()
    model = OrderedLogit().fit(train["elo_diff"].to_numpy(), train["outcome"].to_numpy())
    p_model = model.predict_proba(test["elo_diff"].to_numpy())

    freq = np.bincount(train["outcome"], minlength=3) / len(train)
    p_clim = np.tile(freq, (len(test), 1))
    p_unif = np.full((len(test), 3), 1.0 / 3.0)

    metrics = {
        "uniform": evaluate(p_unif, y_test),
        "climatology": evaluate(p_clim, y_test),
        "elo_ordered_logit": evaluate(p_model, y_test),
    }
    preds = test[["date", "home_team", "away_team", "elo_diff", "outcome"]].copy()
    preds[["p_away", "p_draw", "p_home"]] = p_model
    assert model.thresholds_ is not None and model.beta_ is not None
    params = {
        "beta": model.beta_,
        "theta_away": model.thresholds_[0],
        "theta_draw": model.thresholds_[1],
        "n_train": float(len(train)),
        "n_test": float(len(test)),
    }
    return BacktestResult(metrics=metrics, predictions=preds.reset_index(drop=True), params=params)
