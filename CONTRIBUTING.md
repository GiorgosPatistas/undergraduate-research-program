# Contributing

For local setup (Python venvs, env vars, migrations, running the three services), see [README.md](README.md). This document covers the collaboration workflow only.

## Branching

- `main` is protected: no direct pushes, no force-push, no branch deletion. All changes go through a pull request.
- Branch off `main` using:
  - `feature/<name>` — new functionality (e.g. `feature/appointments`)
  - `fix/<name>` — bug fixes
  - `chore/<name>` — tooling, CI, dependency bumps, docs
- Keep branches scoped to one feature/fix. Don't mix unrelated changes in one PR.
- Delete your branch after it's merged.

## Commits

- Write commit messages in the imperative mood ("Add appointment cancellation", not "Added" or "Adding").
- Keep commits reasonably small and focused; squash fixup commits before opening a PR if they don't add information.

## Pull Requests

- Open a PR into `main` when your branch is ready for review. Fill out the PR template.
- `Backend CI` (Django test suite) must pass before a PR can merge — it runs automatically on any PR touching `backend/`.
- `Frontend CI` and `ML Service CI` also run automatically (build check / import smoke test) but aren't required to merge yet, since those two services don't have real test suites — treat their failures as a signal, not just noise.
- Rebase or merge `main` into your branch if it falls behind before merging.

## Tests

- Backend: `cd backend && python manage.py test` (see [README.md § Running the Tests](README.md#7-running-the-tests)). Add tests for new endpoints/behavior in `backend/accounts/tests.py` or `backend/api/tests.py`.
- Frontend and ML service don't have automated tests yet — manually verify your change against the running app before opening a PR.

## Code style

- Follow the existing patterns in the file/app you're editing rather than introducing a new style.
- No linter is configured for the frontend yet — keep formatting consistent with surrounding code until one is added.
