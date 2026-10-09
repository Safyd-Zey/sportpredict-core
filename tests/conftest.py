import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def raw_matches() -> pd.DataFrame:
    """Small hand-made dataset in the raw (unvalidated) schema."""
    return pd.DataFrame(
        {
            "date": ["2020-01-03", "2020-01-01", "2020-01-02", "2020-01-04", "2020-01-05"],
            "home_team": ["A", "A", "B", "C", "A"],
            "away_team": ["C", "B", "C", "A", "B"],
            "home_score": [1, 2, 0, 3, None],
            "away_score": [1, 0, 0, 1, None],
            "tournament": ["Friendly", "FIFA World Cup", "Friendly", "UEFA Euro", "Friendly"],
            "neutral": ["FALSE", "TRUE", "FALSE", "FALSE", "FALSE"],
        }
    )


@pytest.fixture
def synthetic_matches() -> pd.DataFrame:
    """Matches generated from known team strengths (for backtest tests)."""
    rng = np.random.default_rng(42)
    teams = [f"T{i}" for i in range(12)]
    strength = dict(zip(teams, np.linspace(-1.5, 1.5, len(teams)), strict=True))
    rows = []
    dates = pd.date_range("2010-01-01", periods=3000, freq="D")
    for d in dates:
        h, a = rng.choice(teams, size=2, replace=False)
        lam_h = np.exp(0.2 + 0.4 * (strength[h] - strength[a]))
        lam_a = np.exp(0.0 - 0.4 * (strength[h] - strength[a]))
        rows.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "home_team": h,
                "away_team": a,
                "home_score": rng.poisson(lam_h),
                "away_score": rng.poisson(lam_a),
                "tournament": "Friendly",
                "neutral": "FALSE",
            }
        )
    return pd.DataFrame(rows)
