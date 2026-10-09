import numpy as np
import pytest

from sportpredict.data import validate
from sportpredict.elo import EloConfig, compute_elo, expected_score, goal_multiplier, k_factor


@pytest.mark.parametrize(
    ("tournament", "expected"),
    [
        ("Friendly", 20),
        ("FIFA World Cup", 60),
        ("FIFA World Cup qualification", 40),
        ("UEFA Euro", 50),
        ("Gulf Cup", 30),
    ],
)
def test_k_factor(tournament, expected):
    assert k_factor(tournament, EloConfig()) == expected


@pytest.mark.parametrize(("gd", "g"), [(0, 1.0), (1, 1.0), (-2, 1.5), (3, 1.75), (5, 2.0)])
def test_goal_multiplier(gd, g):
    assert goal_multiplier(gd) == pytest.approx(g)


def test_expected_score_is_symmetric():
    assert expected_score(0) == pytest.approx(0.5)
    assert expected_score(200) + expected_score(-200) == pytest.approx(1.0)


def test_first_match_uses_initial_ratings(raw_matches):
    rated = compute_elo(validate(raw_matches))
    first = rated.iloc[0]
    assert first["elo_home"] == first["elo_away"] == 1500.0
    assert first["elo_diff"] == 0.0  # neutral ground: no home advantage


def test_ratings_are_point_in_time(raw_matches):
    """Changing a later result must not change features of earlier matches."""
    base = compute_elo(validate(raw_matches))
    changed = raw_matches.copy()
    changed.loc[changed["date"] == "2020-01-04", "home_score"] = 0
    other = compute_elo(validate(changed))
    np.testing.assert_allclose(base["elo_diff"].iloc[:3], other["elo_diff"].iloc[:3])


def test_world_cup_win_update(raw_matches):
    rated = compute_elo(validate(raw_matches))
    # Match 1: A beats B 2-0 at a neutral World Cup game.
    # delta = K * G * (W - We) = 60 * 1.5 * (1 - 0.5) = 45, zero-sum for the pair.
    assert rated.iloc[1]["elo_home"] == pytest.approx(1500.0 - 45.0)  # B before match 2
    assert rated.iloc[2]["elo_home"] == pytest.approx(1500.0 + 45.0)  # A before match 3
