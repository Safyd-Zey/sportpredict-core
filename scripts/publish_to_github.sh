#!/usr/bin/env bash
# One-time publication of this repository to GitHub using the GitHub CLI (https://cli.github.com).
# Usage:  gh auth login   (once)   then   bash scripts/publish_to_github.sh
set -euo pipefail

REPO="sportpredict-core"
command -v gh >/dev/null || { echo "Install GitHub CLI first: https://cli.github.com"; exit 1; }
gh auth status >/dev/null
OWNER="$(gh api user -q .login)"
git checkout -q main

# 1. Replace the USERNAME placeholder in links and badges.
if grep -q "USERNAME" README.md CITATION.cff; then
  for f in README.md CITATION.cff; do sed -i.bak "s/USERNAME/${OWNER}/g" "$f" && rm -f "$f.bak"; done
  git add README.md CITATION.cff
  git commit -q -m "docs: set repository links for ${OWNER}"
fi

# 2. Create the public repository and push main, the tag (triggers Release) and the open branch.
gh repo create "${REPO}" --public --source=. --remote=origin \
  --description "Point-in-time Elo ratings and probabilistic football forecasts" --push
git push -q origin v0.1.0
git push -q origin docs/usage-examples
gh repo edit "${OWNER}/${REPO}" --add-topic football,elo-rating,forecasting,python,reproducible-research

# 3. Labels and issues (roadmap and known limitations).
gh label create research --color 5319e7 --description "Research question / experiment" 2>/dev/null || true
gh issue create --title "Ordered logit never predicts a draw as the most likely outcome" \
  --label bug,research --body "Max P(draw) on the 2022–2026 test set is ≈0.31, so draws (22.8 % of matches) are never the argmax. Evaluate a draw-inflated model (e.g. Dixon–Coles / bivariate Poisson) and compare RPS." >/dev/null
gh issue create --title "Add point-in-time form and goal-difference features" --label enhancement,research \
  --body "Rolling form over the last N matches computed strictly before kick-off; compare RPS against Elo-only model." >/dev/null
gh issue create --title "Publish package to PyPI via trusted publishing" --label enhancement \
  --body "Extend release.yml with pypa/gh-action-pypi-publish using OIDC (no API tokens in secrets)." >/dev/null
I4=$(gh issue create --title "Add a quickstart example script" --label documentation \
  --body "New users need a runnable example that prints ratings and forecasts for an upcoming fixture.")

# 4. Pull request from the open branch; CI runs on it automatically.
gh pr create --base main --head docs/usage-examples --title "docs: add quickstart example" \
  --body "Adds examples/quickstart.py and a README section. Closes #${I4##*/}"

echo "Done: https://github.com/${OWNER}/${REPO}"
echo "Open the PR, wait for green CI, then merge it."
