"""Command-line interface: ``sportpredict backtest`` and ``sportpredict ratings``."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sportpredict import __version__
from sportpredict.backtest import backtest
from sportpredict.data import DATASET_URL, load_matches
from sportpredict.elo import compute_elo
from sportpredict.plots import reliability_diagram


def _cmd_backtest(args: argparse.Namespace) -> int:
    matches = load_matches(args.data)
    res = backtest(matches, args.train_start, args.test_start)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"version": __version__, "data": str(args.data), **res.params, "metrics": res.metrics}
    (out / "metrics.json").write_text(json.dumps(report, indent=2))
    res.predictions.to_csv(out / "predictions.csv", index=False)
    reliability_diagram(res.predictions, out / "reliability.png")

    print(f"{'model':<20}{'accuracy':>10}{'brier':>10}{'log_loss':>10}{'rps':>10}")
    for name, m in res.metrics.items():
        print(
            f"{name:<20}{m['accuracy']:>10.4f}{m['brier']:>10.4f}"
            f"{m['log_loss']:>10.4f}{m['rps']:>10.4f}"
        )
    print(f"Results written to {out}/")
    return 0


def _cmd_ratings(args: argparse.Namespace) -> int:
    rated = compute_elo(load_matches(args.data))
    final = rated.attrs["final_ratings"]
    top = sorted(final.items(), key=lambda kv: kv[1], reverse=True)[: args.top]
    for rank, (team, rating) in enumerate(top, start=1):
        print(f"{rank:>3}. {team:<30}{rating:8.1f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sportpredict", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    bt = sub.add_parser("backtest", help="time-based backtest of the Elo model")
    bt.add_argument("--data", default=DATASET_URL, help="CSV path or URL")
    bt.add_argument("--train-start", default="2010-01-01")
    bt.add_argument("--test-start", default="2022-01-01")
    bt.add_argument("--out", default="results")
    bt.set_defaults(func=_cmd_backtest)

    rt = sub.add_parser("ratings", help="print the current top-N Elo ratings")
    rt.add_argument("--data", default=DATASET_URL, help="CSV path or URL")
    rt.add_argument("--top", type=int, default=10)
    rt.set_defaults(func=_cmd_ratings)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
