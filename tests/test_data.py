import pandas as pd
import pytest

from sportpredict.data import AWAY, DRAW, HOME, DataValidationError, load_matches, validate


def test_validate_sorts_drops_unplayed_and_codes_outcome(raw_matches):
    df = validate(raw_matches)
    assert len(df) == 4  # the unplayed fixture is dropped
    assert df["date"].is_monotonic_increasing
    assert df["outcome"].tolist() == [HOME, DRAW, DRAW, HOME]
    assert df["neutral"].tolist() == [True, False, False, False]


def test_missing_column_raises(raw_matches):
    with pytest.raises(DataValidationError, match="missing columns"):
        validate(raw_matches.drop(columns="tournament"))


def test_bad_date_raises(raw_matches):
    raw_matches.loc[0, "date"] = "not-a-date"
    with pytest.raises(DataValidationError, match="date"):
        validate(raw_matches)


def test_negative_score_raises(raw_matches):
    raw_matches.loc[0, "home_score"] = -1
    with pytest.raises(DataValidationError, match="negative"):
        validate(raw_matches)


def test_self_match_raises(raw_matches):
    raw_matches.loc[0, "away_team"] = "A"
    with pytest.raises(DataValidationError, match="itself"):
        validate(raw_matches)


def test_load_matches_from_csv(tmp_path, raw_matches):
    path = tmp_path / "m.csv"
    raw_matches.to_csv(path, index=False)
    df = load_matches(path)
    assert isinstance(df, pd.DataFrame) and AWAY not in df["outcome"].tolist()
