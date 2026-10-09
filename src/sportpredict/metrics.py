"""Scoring rules for three-way probabilistic forecasts.

Columns of ``proba`` are ordered: away win, draw, home win (ordinal scale).
Lower is better for Brier score, log-loss and RPS; higher for accuracy.
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-15


def _check(proba: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    proba = np.asarray(proba, dtype=float)
    y = np.asarray(y, dtype=int)
    if proba.ndim != 2 or proba.shape[1] != 3:
        raise ValueError("proba must have shape (n, 3)")
    if proba.shape[0] != y.shape[0]:
        raise ValueError("proba and y have different lengths")
    if not np.allclose(proba.sum(axis=1), 1.0, atol=1e-6):
        raise ValueError("each row of proba must sum to 1")
    return proba, y


def _one_hot(y: np.ndarray) -> np.ndarray:
    return np.eye(3)[y]


def accuracy(proba: np.ndarray, y: np.ndarray) -> float:
    proba, y = _check(proba, y)
    return float(np.mean(proba.argmax(axis=1) == y))


def brier_score(proba: np.ndarray, y: np.ndarray) -> float:
    """Multi-class Brier score (Brier, 1950): mean of sum of squared errors."""
    proba, y = _check(proba, y)
    return float(np.mean(np.sum((proba - _one_hot(y)) ** 2, axis=1)))


def log_loss(proba: np.ndarray, y: np.ndarray) -> float:
    proba, y = _check(proba, y)
    p = np.clip(proba[np.arange(len(y)), y], _EPS, 1.0)
    return float(-np.mean(np.log(p)))


def ranked_probability_score(proba: np.ndarray, y: np.ndarray) -> float:
    """RPS (Epstein, 1969) - the standard score for ordinal football outcomes."""
    proba, y = _check(proba, y)
    cum_p = np.cumsum(proba, axis=1)[:, :-1]
    cum_o = np.cumsum(_one_hot(y), axis=1)[:, :-1]
    return float(np.mean(np.sum((cum_p - cum_o) ** 2, axis=1) / 2.0))


def evaluate(proba: np.ndarray, y: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": accuracy(proba, y),
        "brier": brier_score(proba, y),
        "log_loss": log_loss(proba, y),
        "rps": ranked_probability_score(proba, y),
    }
