import numpy as np
import pytest

from sportpredict.metrics import (
    accuracy,
    brier_score,
    evaluate,
    log_loss,
    ranked_probability_score,
)
from sportpredict.model import OrderedLogit

PERFECT = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)
Y = np.array([2, 0, 1])


def test_perfect_forecast_scores():
    assert accuracy(PERFECT, Y) == 1.0
    assert brier_score(PERFECT, Y) == 0.0
    assert ranked_probability_score(PERFECT, Y) == 0.0
    assert log_loss(PERFECT, Y) == pytest.approx(0.0, abs=1e-12)


def test_uniform_forecast_known_values():
    p = np.full((3, 3), 1 / 3)
    assert brier_score(p, Y) == pytest.approx(2 / 3)
    assert log_loss(p, Y) == pytest.approx(np.log(3))


def test_rps_penalises_distant_errors_more():
    y = np.array([2])
    near = np.array([[0.0, 1.0, 0.0]])  # predicted draw, home won
    far = np.array([[1.0, 0.0, 0.0]])  # predicted away win, home won
    assert ranked_probability_score(far, y) > ranked_probability_score(near, y)


@pytest.mark.parametrize(
    "proba",
    [np.ones((3, 2)) / 2, np.ones((2, 3)) / 3, np.array([[0.5, 0.5, 0.5]] * 3)],
)
def test_invalid_inputs_raise(proba):
    with pytest.raises(ValueError):
        brier_score(proba, Y)


def test_evaluate_returns_all_metrics():
    assert set(evaluate(PERFECT, Y)) == {"accuracy", "brier", "log_loss", "rps"}


def test_ordered_logit_recovers_monotone_relationship():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 200, 5000)
    true = OrderedLogit()
    true.beta_, true.thresholds_ = 0.6, (-0.6, 0.5)
    p = true.predict_proba(x)
    y = np.array([rng.choice(3, p=row) for row in p])

    model = OrderedLogit().fit(x, y)
    assert model.beta_ == pytest.approx(0.6, abs=0.05)
    probs = model.predict_proba(np.array([-400.0, 0.0, 400.0]))
    np.testing.assert_allclose(probs.sum(axis=1), 1.0)
    assert probs[2, 2] > probs[1, 2] > probs[0, 2]  # P(home) grows with elo_diff


def test_ordered_logit_errors():
    with pytest.raises(RuntimeError):
        OrderedLogit().predict_proba(np.array([0.0]))
    with pytest.raises(ValueError):
        OrderedLogit().fit(np.array([0.0, 1.0]), np.array([0]))
    with pytest.raises(ValueError):
        OrderedLogit().fit(np.array([0.0]), np.array([3]))
