# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [SemVer](https://semver.org/).

## [0.2.0] - 2026-10-21
### Added
- REST API (FastAPI): `/health`, `/v1/ratings`, `/v1/predict`; CLI command `sportpredict serve`.
- Dockerfile: multi-stage build, non-root user, health check, dataset verified by SHA-256.
- Jenkins pipeline (`Jenkinsfile`): lint, unit tests with JUnit/coverage reports, hadolint,
  image build, container smoke test, optional Docker Hub push, deployment to Kubernetes (kind)
  with verification and automatic rollback.
- Jenkins controller as code (`jenkins/`): pinned LTS image, plugins, JCasC, Job DSL.
- Kubernetes manifests (`k8s/`): Deployment with probes, limits and rolling update; NodePort Service.

## [0.1.0] - 2026-10-09
### Added
- Data loading and schema validation for the `international_results` dataset (pinned commit).
- Point-in-time Elo ratings (eloratings.net K factors and goal-difference multiplier).
- Ordered logistic regression mapping Elo difference to P(away / draw / home).
- Scoring rules: accuracy, multi-class Brier score, log-loss, ranked probability score.
- Time-based backtest with uniform and climatology baselines, reliability diagram.
- CLI: `sportpredict backtest`, `sportpredict ratings`.
- CI (lint, test matrix, build, reproducible experiment) and tag-based release workflow.
