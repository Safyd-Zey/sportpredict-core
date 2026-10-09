# Contributing

The project follows **GitHub Flow**:

1. Open an issue describing the bug or research idea.
2. Create a branch from `main`: `feature/<short-name>`, `fix/<short-name>` or `docs/<short-name>`.
3. Commit with [Conventional Commits](https://www.conventionalcommits.org/) messages
   (`feat:`, `fix:`, `test:`, `docs:`, `ci:`, `chore:`).
4. Run checks locally:
   ```bash
   pip install -e ".[dev]"
   ruff check . && ruff format --check .
   pytest
   ```
5. Open a pull request that references the issue (`Closes #N`). CI must be green before merge.

**Scientific rule:** every feature must be computable from information available
*before* kick-off. Add a test that changing a later result does not change earlier features.
