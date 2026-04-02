---
status: awaiting_human_verify
trigger: "Investigate issue: model-not-loaded-lightgbm\n\nSummary: FastAPI startup/runtime logs `ModelNotLoadedError` when loading prediction model due to missing `lightgbm` module."
created: 2026-04-02T19:18:00Z
updated: 2026-04-02T20:03:00Z
---

## Current Focus

hypothesis: Repository-side dependency declarations are now complete; remaining failure requires user runtime to reinstall/sync dependencies in the actual serving environment.
test: User performs dependency sync in failing runtime and re-tests prediction endpoint.
expecting: Runtime can import lightgbm; prediction endpoint no longer returns 503 due to ModelNotLoadedError.
next_action: request human action to reinstall dependencies and verify endpoint behavior

## Symptoms

expected: Prediction model loads successfully and prediction endpoints are available.
actual: App logs `ModelNotLoadedError` and model load fails.
errors: `Failed to load model from app\\features\\prediction\\ml_models\\lightgbm_model_forex.pkl: No module named 'lightgbm'`
reproduction: Start app (or trigger model loading path) in current environment.
started: Reported now (2026-04-02); prior working state unknown.

## Eliminated

- hypothesis: Updating only environment.yml is sufficient to fix all runtime contexts.
  evidence: User re-test still returns 503 with `No module named 'lightgbm'` during prediction path.
  timestamp: 2026-04-02T19:52:00Z

## Evidence

- timestamp: 2026-04-02T19:19:00Z
  checked: .planning/debug/knowledge-base.md
  found: Knowledge base file does not exist yet.
  implication: No prior known-pattern entry available; proceed with normal investigation.

- timestamp: 2026-04-02T19:20:00Z
  checked: app/features/prediction/service.py
  found: ModelLoader._load_model uses joblib.load(model_path) and wraps ImportError into ModelNotLoadedError with underlying message.
  implication: Missing model class dependencies (e.g., lightgbm) directly surface as current symptom.

- timestamp: 2026-04-02T19:20:00Z
  checked: app/core/config.py
  found: MODEL_FILENAME is explicitly lightgbm_model_forex.pkl.
  implication: Service is designed to load a LightGBM-trained artifact.

- timestamp: 2026-04-02T19:20:00Z
  checked: environment.yml
  found: Dependency list omits lightgbm while including joblib/scikit-learn/ta/FastAPI packages.
  implication: Fresh environments from declared dependencies will not provide lightgbm for unpickling model.

- timestamp: 2026-04-02T19:20:00Z
  checked: app/features/prediction/ml_models/MODEL_USAGE.md
  found: Documentation states the artifact is a saved LightGBM model.
  implication: Confirms runtime requires lightgbm presence, matching error text.

- timestamp: 2026-04-02T19:22:00Z
  checked: `python -c "import lightgbm; print(lightgbm.__version__)"`
  found: Current shell has lightgbm installed (4.6.0).
  implication: Symptom is environment-specific; however dependency manifest omission still explains failures in freshly provisioned runtimes.

- timestamp: 2026-04-02T19:26:00Z
  checked: `python -c "from app.features.prediction.service import ModelLoader; m = ModelLoader().get_model(); print(type(m).__name__)"`
  found: Model loads successfully as LGBMClassifier; no ModelNotLoadedError (only sklearn version warning).
  implication: Code path is healthy when lightgbm dependency is present.

- timestamp: 2026-04-02T19:50:00Z
  checked: human verification response
  found: Runtime still fails with `ModelNotLoadedError ... No module named 'lightgbm'`; prediction endpoint returns 503.
  implication: Initial fix did not reach failing runtime; dependency declaration and/or runtime install path still incomplete.

- timestamp: 2026-04-02T19:53:00Z
  checked: repository runtime config files
  found: No Dockerfile, compose, requirements.txt, or shell/PowerShell startup scripts in repo root.
  implication: Runtime may depend on manual command invocation; interpreter mismatch is a strong candidate.

- timestamp: 2026-04-02T19:55:00Z
  checked: interpreter/runtime probes (`python`, `uvicorn`)
  found: `python` points to miniconda base; `uvicorn` command and `python -m uvicorn` are unavailable in this shell.
  implication: Confirms dependency/runtime invocation inconsistency risk across environments.

- timestamp: 2026-04-02T19:57:00Z
  checked: `python -m pip install -r requirements.txt`
  found: Command fails because `requirements.txt` is missing from repository.
  implication: Documented pip setup path is broken; users may run app without full declared deps, including lightgbm.

- timestamp: 2026-04-02T20:00:00Z
  checked: requirements.txt creation
  found: Added canonical pip dependency manifest including `lightgbm==4.6.0` and runtime dependencies (`uvicorn`, `fastapi`, etc.).
  implication: Both documented setup paths (conda + pip) now declare lightgbm.

- timestamp: 2026-04-02T20:01:00Z
  checked: `python -m pip install --dry-run lightgbm==4.6.0`
  found: Package resolves successfully in current environment.
  implication: pip path can provide lightgbm when executed in target runtime.

## Resolution

root_cause:
  Dependency provisioning was incomplete across supported setup paths: `environment.yml` previously omitted lightgbm, and the documented pip install path (`pip install -r requirements.txt`) was non-functional because `requirements.txt` did not exist. This allows runtimes to start without lightgbm and fail model unpickling with `No module named 'lightgbm'`.
fix:
  Added `lightgbm==4.6.0` to `environment.yml`; now also add a canonical `requirements.txt` including lightgbm and all app runtime dependencies.
verification:
  Repository-level verification complete (manifest exists and includes required package), but end-to-end runtime verification is pending user dependency sync in the failing environment.
files_changed:
  - environment.yml
  - requirements.txt
