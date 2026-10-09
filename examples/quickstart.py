"""Quickstart: fit the model on all history and forecast a hypothetical fixture.

Run:  python examples/quickstart.py "Kazakhstan" "Norway" [--neutral]
"""

import sys

from sportpredict.data import load_matches
from sportpredict.elo import EloConfig, compute_elo
from sportpredict.model import OrderedLogit


def main() -> None:
    home, away = sys.argv[1], sys.argv[2]
    neutral = "--neutral" in sys.argv
    cfg = EloConfig()

    rated = compute_elo(load_matches(), cfg)
    recent = rated[rated["date"] >= "2010-01-01"]
    model = OrderedLogit().fit(recent["elo_diff"].to_numpy(), recent["outcome"].to_numpy())

    ratings = rated.attrs["final_ratings"]
    diff = ratings[home] - ratings[away] + (0.0 if neutral else cfg.home_advantage)
    p_away, p_draw, p_home = model.predict_proba([diff])[0]
    print(f"{home} {ratings[home]:.0f} vs {away} {ratings[away]:.0f}")
    print(f"P(home)={p_home:.2f}  P(draw)={p_draw:.2f}  P(away)={p_away:.2f}")


if __name__ == "__main__":
    main()
