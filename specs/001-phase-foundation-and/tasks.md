# Tasks: Phase 0 — Foundation and Platform Readiness

**Input**: Design documents from `/specs/001-phase-foundation-and/`
**Prerequisites**: plan.md, spec.md

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 [P] [Setup] Create backend project structure under `backend/src/` and `backend/tests/`
- [x] T002 [P] [Setup] Create initial project README or quickstart notes for local development
- [x] T003 [P] [Setup] Add `.gitignore` entries for environment files, logs, and temporary data
- [x] T004 [P] [Setup] Add baseline app entrypoint placeholder at `backend/src/app-entrypoint`
- [x] T005 [P] [Setup] Add `specs/001-phase-foundation-and/plan.md` and `specs/001-phase-foundation-and/spec.md` references where needed

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T006 [P] [Foundational] Add environment configuration loader in `backend/src/config/`
- [x] T007 [Foundational] Document required startup variables and secret names in `backend/src/config/README.md` or `backend/README.md`
- [x] T008 [P] [Foundational] Add fail-fast startup validation for missing required config values
- [x] T009 [Foundational] Add logging configuration and startup diagnostics in `backend/src/`
- [x] T010 [Foundational] Add a health/status endpoint and dependency check scaffolding in `backend/src/health/`
- [x] T011 [Foundational] Add webhook receiver skeleton in `backend/src/webhooks/`
- [x] T012 [Foundational] Add request verification utility for webhook signatures in `backend/src/webhooks/`
- [x] T013 [Foundational] Add scheduler/worker skeleton in `backend/src/scheduler/`
- [x] T014 [Foundational] Add bilingual content lookup rules and fallback behavior in `backend/src/i18n/`
- [x] T015 [Foundational] Document the Phase 0 architecture, adapter boundaries, and integration touchpoints in `specs/001-phase-foundation-and/plan.md` or `specs/001-phase-foundation-and/research.md`

---

## Phase 3: User Story 1 - Run local platform health check (Priority: P1)

**Goal**: Ensure developers can start the app and verify platform health.

- [x] T016 [US1] Implement `/health` endpoint in `backend/src/health/`
- [x] T017 [US1] Add a health check integration test in `backend/tests/integration/test_health.py`
- [x] T018 [US1] Add a simple local startup validation test in `backend/tests/unit/test_config_validation.py`
- [x] T019 [US1] Document health endpoint usage and expected response in `backend/README.md`

---

## Phase 4: User Story 2 - Validate webhook authenticity skeleton (Priority: P1)

**Goal**: Add secure webhook verification without wiring business logic.

- [x] T020 [US2] Implement webhook request entrypoint in `backend/src/webhooks/receiver`
- [x] T021 [US2] Implement signature verification utility in `backend/src/webhooks/signature.py`
- [x] T022 [US2] Add tests for valid and invalid webhook signatures in `backend/tests/unit/test_webhook_signature.py`
- [x] T023 [US2] Document webhook verification format and test procedure in `backend/README.md`

---

## Phase 5: User Story 3 - Use secure environment configuration (Priority: P2)

**Goal**: Ensure configuration and secrets are loaded securely and fail fast.

- [x] T024 [US3] Implement env config loader in `backend/src/config/loader.py`
- [x] T025 [US3] Add config validation rules for required values in `backend/src/config/validate.py`
- [x] T026 [US3] Add unit tests for missing config values and expected errors in `backend/tests/unit/test_config_loader.py`
- [x] T027 [US3] Document environment variable requirements and startup behavior in `backend/README.md`

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T028 [P] [Polish] Add or update `quickstart.md` with setup and run instructions for Phase 0
- [x] T029 [P] [Polish] Add documentation for bilingual content conventions in `backend/src/i18n/README.md`
- [x] T030 [P] [Polish] Review and refine Phase 0 artifacts for completeness and clarity
- [x] T031 [P] [Polish] Confirm plan/spec consistency and update `specs/001-phase-foundation-and/plan.md` if needed

---

## Status

All Phase 0 foundation tasks are implemented and verified against the codebase:
- `backend/src/{config,health,webhooks,scheduler,i18n}/` — source modules
- `backend/tests/{unit,integration}/` — unit + integration coverage
- `backend/README.md` and `backend/src/config/README.md` — docs

See `../002-phase-merchant-install/` (Phase 1 MVP + Full) for merchant onboarding work built on this foundation.
