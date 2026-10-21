"""REST API serving Elo ratings and outcome probabilities (FastAPI).

The model is fitted once at start-up on the configured dataset; requests only
read precomputed ratings, so a response never runs the training loop.
Run with ``sportpredict serve`` or ``uvicorn sportpredict.api:app``.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from sportpredict import __version__
from sportpredict.data import DATASET_URL, load_matches
from sportpredict.elo import EloConfig, compute_elo
from sportpredict.model import OrderedLogit

DATA_ENV = "SPORTPREDICT_DATA"
TRAIN_START_ENV = "SPORTPREDICT_TRAIN_START"


@dataclass
class ServingState:
    ratings: dict[str, float]
    model: OrderedLogit
    cfg: EloConfig
    n_matches: int
    data_until: str
    generated_at: str


def build_state(source: str | Path, train_start: str = "2010-01-01") -> ServingState:
    """Load matches, compute ratings and fit the outcome model."""
    cfg = EloConfig()
    rated = compute_elo(load_matches(source), cfg)
    train = rated[rated["date"] >= train_start]
    model = OrderedLogit().fit(train["elo_diff"].to_numpy(), train["outcome"].to_numpy())
    return ServingState(
        ratings=rated.attrs["final_ratings"],
        model=model,
        cfg=cfg,
        n_matches=len(rated),
        data_until=rated["date"].max().date().isoformat(),
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def create_app(source: str | Path | None = None, train_start: str | None = None) -> FastAPI:
    source = source or os.environ.get(DATA_ENV, DATASET_URL)
    train_start = train_start or os.environ.get(TRAIN_START_ENV, "2010-01-01")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.serving = build_state(source, train_start)
        yield

    app = FastAPI(title="SportPredict API", version=__version__, lifespan=lifespan)

    def state() -> ServingState:
        return app.state.serving

    @app.get("/health")
    def health() -> dict:
        s = state()
        return {
            "status": "ok",
            "version": __version__,
            "matches": s.n_matches,
            "data_until": s.data_until,
            "generated_at": s.generated_at,
        }

    @app.get("/v1/ratings")
    def ratings(top: int = Query(10, ge=1, le=300)) -> list[dict]:
        ranked = sorted(state().ratings.items(), key=lambda kv: kv[1], reverse=True)[:top]
        return [
            {"rank": i, "team": team, "rating": round(r, 1)}
            for i, (team, r) in enumerate(ranked, start=1)
        ]

    @app.get("/v1/predict")
    def predict(home: str, away: str, neutral: bool = False) -> dict:
        s = state()
        unknown = [t for t in (home, away) if t not in s.ratings]
        if unknown:
            raise HTTPException(status_code=404, detail=f"unknown team(s): {unknown}")
        if home == away:
            raise HTTPException(status_code=422, detail="home and away must differ")
        diff = s.ratings[home] - s.ratings[away] + (0.0 if neutral else s.cfg.home_advantage)
        p_away, p_draw, p_home = s.model.predict_proba([diff])[0]
        return {
            "home": home,
            "away": away,
            "neutral": neutral,
            "elo_diff": round(diff, 1),
            "probabilities": {
                "home_win": round(float(p_home), 4),
                "draw": round(float(p_draw), 4),
                "away_win": round(float(p_away), 4),
            },
            "model_version": __version__,
            "data_until": s.data_until,
        }

    return app


app = create_app()
