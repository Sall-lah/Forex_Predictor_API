# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 -- MVP

**Shipped:** 2026-03-31
**Phases:** 3 | **Plans:** 6 | **Sessions:** 1

### What Was Built
- Implemented a production-ready token-bucket rate limiter with typed contracts, monotonic refill math, and deterministic decision payloads.
- Added async-safe in-memory storage with TTL cleanup and max-entry guardrails, plus endpoint-aware policy selection.
- Wired global FastAPI middleware with trusted-proxy-aware IP handling, exempt-path normalization, and standards-compliant 429/headers behavior.
- Added security/performance/memory regression tests and operator/developer documentation for extension and anti-bypass behavior.

### What Worked
- Wave-based execution across planning and implementation enabled fast, traceable delivery from requirements to verified outcomes.
- TDD-style red/green commits at plan level kept behavior changes measurable and reduced ambiguity during verification.

### What Was Inefficient
- Planning metadata handling required extra repair when `.planning` tracking and state format drifted.
- Duplicate summary artifacts in Phase 1 increased noise in completion accounting.

### Patterns Established
- Rate-limit changes should ship with coupled updates: implementation, docs, and middleware regression tests.
- Trusted proxy and exemption behavior must remain centralized in service logic and operator docs.

### Key Lessons
1. Keep planning metadata in version control from day one to avoid workflow-state divergence.
2. Use deterministic clocks and atomic decision objects for rate-limit math to keep headers and deny behavior consistent.

### Cost Observations
- Model mix: Not tracked in-repo for v1.0
- Sessions: 1 milestone execution cycle
- Notable: Most cost came from verification/state tooling overhead, not core feature implementation.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 1 | 3 | Established end-to-end GSD flow (plan -> execute -> verify -> archive) |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | middleware, bucket, storage, performance suites | Focused phase requirements fully verified | 0 |

### Top Lessons (Verified Across Milestones)

1. Documentation and security behavior must evolve together to prevent policy drift.
2. Planning-state hygiene is critical for smooth milestone operations.
