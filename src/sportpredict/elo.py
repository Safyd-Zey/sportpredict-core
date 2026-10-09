"""Point-in-time Elo ratings for national football teams.

The update rule follows the World Football Elo Ratings (eloratings.net):
the K factor depends on the tournament and is scaled by the goal difference.
Every match receives the ratings *before* it is played, so the resulting
features never contain information from the future (no data leakage).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EloConfig:
    initial_rating: float = 1500.0
    home_advantage: float = 100.0
    k_world_cup: float = 60.0
    k_continental: float = 50.0
    k_qualifier: float = 40.0
    k_other: float = 30.0
    k_friendly: float = 20.0


_CONTINENTAL = (
    "UEFA Euro",
    "Copa América",
    "African Cup of Nations",
    "AFC Asian Cup",
    "Gold Cup",
    "Confederations Cup",
)


def k_factor(tournament: str, cfg: EloConfig) -> float:
    """Return the base K factor for a tournament name."""
    t = str(tournament)
    if t == "Friendly":
        return cfg.k_friendly
    if "qualification" in t:
        return cfg.k_qualifier
    if t == "FIFA World Cup":
        return cfg.k_world_cup
    if t in _CONTINENTAL:
        return cfg.k_continental
    return cfg.k_other


def goal_multiplier(goal_diff: int) -> float:
    """Goal-difference multiplier G used by eloratings.net."""
    n = abs(int(goal_diff))
    if n <= 1:
        return 1.0
    if n == 2:
        return 1.5
    return (11 + n) / 8


def expected_score(rating_diff: float | np.ndarray) -> float | np.ndarray:
    """Expected score of the first team given (its rating - opponent rating)."""
    return 1.0 / (1.0 + 10 ** (-np.asarray(rating_diff) / 400.0))


def compute_elo(matches: pd.DataFrame, cfg: EloConfig | None = None) -> pd.DataFrame:
    """Add pre-match ratings and the effective rating difference to ``matches``.

    New columns: ``elo_home``, ``elo_away`` (ratings before kick-off) and
    ``elo_diff`` = elo_home - elo_away + home advantage (0 on neutral ground).
    Ratings after the last match are stored in ``out.attrs["final_ratings"]``.
    The input must be sorted by date (``data.validate`` guarantees this).
    """
    cfg = cfg or EloConfig()
    ratings: dict[str, float] = {}
    n = len(matches)
    pre_home = np.empty(n)
    pre_away = np.empty(n)
    diffs = np.empty(n)

    rows = zip(
        matches["home_team"],
        matches["away_team"],
        matches["home_score"],
        matches["away_score"],
        matches["tournament"],
        matches["neutral"],
        strict=True,
    )
    for i, (home, away, hs, as_, tournament, neutral) in enumerate(rows):
        r_h = ratings.get(home, cfg.initial_rating)
        r_a = ratings.get(away, cfg.initial_rating)
        diff = r_h - r_a + (0.0 if neutral else cfg.home_advantage)
        pre_home[i], pre_away[i], diffs[i] = r_h, r_a, diff

        actual = 1.0 if hs > as_ else 0.5 if hs == as_ else 0.0
        delta = (
            k_factor(tournament, cfg) * goal_multiplier(hs - as_) * (actual - expected_score(diff))
        )
        ratings[home] = r_h + delta
        ratings[away] = r_a - delta

    out = matches.copy()
    out["elo_home"] = pre_home
    out["elo_away"] = pre_away
    out["elo_diff"] = diffs
    out.attrs["final_ratings"] = dict(ratings)  # ratings after the last match
    return out
