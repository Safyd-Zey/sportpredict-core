from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sportpredict import __version__
from sportpredict.api import create_app

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_matches.csv"


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app(SAMPLE, train_start="2016-01-01")) as c:
        yield c


def test_health_reports_model_metadata(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["matches"] > 0
    assert body["data_until"] >= "2025-01-01"


def test_ratings_are_sorted_and_limited(client):
    rows = client.get("/v1/ratings", params={"top": 5}).json()
    assert [r["rank"] for r in rows] == [1, 2, 3, 4, 5]
    ratings = [r["rating"] for r in rows]
    assert ratings == sorted(ratings, reverse=True)


def test_ratings_rejects_invalid_top(client):
    assert client.get("/v1/ratings", params={"top": 0}).status_code == 422


def test_predict_returns_probabilities_summing_to_one(client):
    top = client.get("/v1/ratings", params={"top": 2}).json()
    strong, weaker = top[0]["team"], top[1]["team"]
    body = client.get("/v1/predict", params={"home": strong, "away": weaker}).json()
    p = body["probabilities"]
    assert sum(p.values()) == pytest.approx(1.0, abs=1e-3)
    assert p["home_win"] > p["away_win"]  # stronger team at home
    assert body["model_version"] == __version__


def test_home_advantage_is_removed_on_neutral_ground(client):
    top = client.get("/v1/ratings", params={"top": 2}).json()
    params = {"home": top[0]["team"], "away": top[1]["team"]}
    home = client.get("/v1/predict", params=params).json()
    neutral = client.get("/v1/predict", params={**params, "neutral": True}).json()
    assert home["elo_diff"] - neutral["elo_diff"] == pytest.approx(100.0)


def test_predict_unknown_team_is_404(client):
    r = client.get("/v1/predict", params={"home": "Atlantis", "away": "Brazil"})
    assert r.status_code == 404


def test_predict_same_team_is_422(client):
    team = client.get("/v1/ratings", params={"top": 1}).json()[0]["team"]
    r = client.get("/v1/predict", params={"home": team, "away": team})
    assert r.status_code == 422
