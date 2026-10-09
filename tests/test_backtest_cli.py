import json
from pathlib import Path

import pytest

from sportpredict.backtest import backtest
from sportpredict.cli import main
from sportpredict.data import validate
from sportpredict.plots import calibration_table

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_matches.csv"


def test_model_beats_baselines_on_synthetic_data(synthetic_matches):
    res = backtest(validate(synthetic_matches), "2012-01-01", "2016-01-01")
    m = res.metrics
    assert m["elo_ordered_logit"]["rps"] < m["climatology"]["rps"] < m["uniform"]["rps"]
    assert res.params["beta"] > 0
    assert len(res.predictions) == res.params["n_test"]


def test_backtest_rejects_bad_periods(synthetic_matches):
    df = validate(synthetic_matches)
    with pytest.raises(ValueError, match="earlier"):
        backtest(df, "2016-01-01", "2012-01-01")
    with pytest.raises(ValueError, match="empty"):
        backtest(df, "2030-01-01", "2031-01-01")


def test_calibration_table_bins():
    import numpy as np

    tab = calibration_table(np.array([0.05, 0.15, 0.95, 1.0]), np.array([0, 0, 1, 1]), n_bins=10)
    assert tab["n"].sum() == 4
    assert tab["bin"].max() == 9


def test_cli_backtest_on_sample_data(tmp_path, capsys):
    code = main(
        [
            "backtest",
            "--data",
            str(SAMPLE),
            "--train-start",
            "2018-01-01",
            "--test-start",
            "2023-01-01",
            "--out",
            str(tmp_path),
        ]
    )
    assert code == 0
    report = json.loads((tmp_path / "metrics.json").read_text())
    assert report["metrics"]["elo_ordered_logit"]["accuracy"] > 0.5
    assert (tmp_path / "reliability.png").stat().st_size > 0
    assert "elo_ordered_logit" in capsys.readouterr().out


def test_cli_ratings(capsys):
    assert main(["ratings", "--data", str(SAMPLE), "--top", "3"]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 3
