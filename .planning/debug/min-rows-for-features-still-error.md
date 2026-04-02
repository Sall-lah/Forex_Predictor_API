---
status: awaiting_human_verify
trigger: "Investigate issue: min-rows-for-features-still-error"
created: 2026-04-02T00:00:00Z
updated: 2026-04-02T00:10:30Z
---

## Current Focus

hypothesis: Fix applied; original failure should be gone when running real prediction path.
test: Have user run original reproduction flow in real environment.
expecting: No "Need at least 168 rows..." error for 73-row input; request proceeds past minimum-row validation.
next_action: Await human verification on actual workflow/API request.

## Symptoms

expected: With MIN_ROWS_FOR_FEATURES set to 38, a dataset with 73 rows should pass feature-extraction minimum-row validation.
actual: Validation still fails and request is rejected.
errors: "Need at least 168 rows for feature extraction, got 73"
reproduction: Run the feature extraction / prediction path with input that yields 73 rows after setting config value to 38 in config.py.
started: Issue observed after changing MIN_ROWS_FOR_FEATURES from 168 to 38; still reproduces now.

## Eliminated

## Evidence

- timestamp: 2026-04-02T00:01:30Z
  checked: .planning/debug/knowledge-base.md
  found: Knowledge base file does not exist.
  implication: No prior known-pattern candidate available; continue normal investigation.

- timestamp: 2026-04-02T00:03:20Z
  checked: code search for error text and MIN_ROWS_FOR_FEATURES references
  found: Error is raised in app/features/prediction/service.py using settings.MIN_ROWS_FOR_FEATURES; config default currently 38 in app/core/config.py.
  implication: No hardcoded 168 in service; runtime value likely overridden externally.

- timestamp: 2026-04-02T00:05:40Z
  checked: file search for env files and MIN_ROWS_FOR_FEATURES usage
  found: Repository contains .env with MIN_ROWS_FOR_FEATURES reference line.
  implication: High-probability external override source exists.

- timestamp: 2026-04-02T00:07:10Z
  checked: .env file content
  found: MIN_ROWS_FOR_FEATURES=168 is explicitly set in .env.
  implication: This overrides Settings default value in config.py.

- timestamp: 2026-04-02T00:07:40Z
  checked: runtime settings evaluation via python one-liner
  found: get_settings().MIN_ROWS_FOR_FEATURES prints 168.
  implication: Root cause confirmed: environment override keeps threshold at 168.

- timestamp: 2026-04-02T00:09:20Z
  checked: runtime settings after .env update
  found: get_settings().MIN_ROWS_FOR_FEATURES prints 38.
  implication: Effective runtime threshold now matches intended value.

- timestamp: 2026-04-02T00:09:50Z
  checked: OHLCVPreprocessor.validate_input with synthetic 73-row dataframe
  found: validate_input passes successfully with no InsufficientDataError.
  implication: Minimum-row guard now permits 73 rows.

## Resolution

root_cause: app/core/config.py default (38) is overridden by .env value MIN_ROWS_FOR_FEATURES=168, and prediction validation reads the effective runtime Settings value.
fix: Update .env MIN_ROWS_FOR_FEATURES from 168 to 38 so runtime threshold matches intended minimum.
verification: Runtime settings now resolve MIN_ROWS_FOR_FEATURES=38, and pre-validation accepts 73 rows in direct service-level check.
files_changed: [.env]
