# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [SemVer](https://semver.org/).

## [0.1.0] - 2026-10-09
### Added
- Data loading and schema validation for the `international_results` dataset (pinned commit).
- Point-in-time Elo ratings (eloratings.net K factors and goal-difference multiplier).
- Ordered logistic regression mapping Elo difference to P(away / draw / home).
- Scoring rules: accuracy, multi-class Brier score, log-loss, ranked probability score.
- Time-based backtest with uniform and climatology baselines, reliability diagram.
- CLI: `sportpredict backtest`, `sportpredict ratings`.
- CI (lint, test matrix, build, reproducible experiment) and tag-based release workflow.
