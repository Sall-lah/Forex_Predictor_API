# Deferred Items (Out of Scope)

These items were observed during 01-01 execution but are unrelated to the current task scope and were intentionally not modified.

- Generated cache artifacts under `__pycache__/` directories (`app/**/__pycache__`, `tests/**/__pycache__`).
- Additional generated cache artifacts under `app/shared/**/__pycache__` observed during plan 01-03 verification.
- Untracked local model artifact: `app/features/prediction/ml_models/lightgbm_model_forex_new.pkl`.
- Pre-existing unstaged documentation changes:
  - `app/features/prediction/ml_models/MODEL_USAGE.md`
  - `app/features/prediction/ml_models/OHLCV_PREPROCESS.md`
