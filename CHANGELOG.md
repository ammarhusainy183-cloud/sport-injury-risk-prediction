# Changelog

## [Unreleased]
- Fixed frontend bug where JavaScript was accidentally embedded inside CSS in `templates/dashboard.html`.
- Rewrote coach UI functions (`loadCoachAthletes`, `viewAthleteDetails`) to be robust and handle errors/loading states.
- Added end-to-end smoke test `scripts/e2e_test.py` to validate registration, profile creation, exercise logging, assessment, and coach flows.
- Added GitHub Actions workflow `.github/workflows/ci.yml` to run unit tests and smoke tests on push/PR.
