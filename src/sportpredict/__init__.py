"""SportPredict Core: point-in-time Elo ratings and probabilistic forecasts
of football match outcomes (home win / draw / away win)."""

__version__ = "0.1.0"

from sportpredict.elo import EloConfig, compute_elo
from sportpredict.metrics import accuracy, brier_score, log_loss, ranked_probability_score
from sportpredict.model import OrderedLogit

__all__ = [
    "EloConfig",
    "OrderedLogit",
    "__version__",
    "accuracy",
    "brier_score",
    "compute_elo",
    "log_loss",
    "ranked_probability_score",
]
