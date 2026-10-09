"""Loading and validation of match data.

Expected schema (international_results dataset, CC0):
date, home_team, away_team, home_score, away_score, tournament, city, country, neutral
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATASET_COMMIT = "b7a3a8ee5d37780c6a03101c188658fd439e241d"
DATASET_URL = (
    f"https://raw.githubusercontent.com/martj42/international_results/{DATASET_COMMIT}/results.csv"
)
REQUIRED_COLUMNS = (
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "tournament",
    "neutral",
)

# Outcome coding is ordinal: 0 = away win, 1 = draw, 2 = home win.
AWAY, DRAW, HOME = 0, 1, 2


class DataValidationError(ValueError):
    """Raised when the input data violate the expected schema."""


def load_matches(source: str | Path = DATASET_URL) -> pd.DataFrame:
    """Read a CSV file (local path or URL) and return validated, sorted matches."""
    df = pd.read_csv(source)
    return validate(df)


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Check the schema, drop unplayed matches and add the ``outcome`` column."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(f"missing columns: {missing}")

    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], format="ISO8601", errors="coerce")
    if out["date"].isna().any():
        raise DataValidationError("unparseable values in 'date'")

    # Scheduled but not yet played fixtures have empty scores.
    out = out.dropna(subset=["home_score", "away_score"])
    if ((out["home_score"] < 0) | (out["away_score"] < 0)).any():
        raise DataValidationError("negative scores found")
    if (out["home_team"] == out["away_team"]).any():
        raise DataValidationError("a team cannot play against itself")

    out["home_score"] = out["home_score"].astype(int)
    out["away_score"] = out["away_score"].astype(int)
    out["neutral"] = out["neutral"].astype(str).str.upper().isin(["TRUE", "1"])
    out["outcome"] = np.select(
        [out["home_score"] > out["away_score"], out["home_score"] == out["away_score"]],
        [HOME, DRAW],
        default=AWAY,
    )
    # Stable sort keeps the original order of matches played on the same day.
    return out.sort_values("date", kind="mergesort").reset_index(drop=True)
