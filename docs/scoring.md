# Candidate scoring module

This module implements safe, evidence‑ready candidate scoring for oil spill investigations.

## Key principles

- Candidate scores are **decision support only**, not legal conclusions.
- Persistence is allowed **only** when `compatibility_state == "compatible"`.
- The current test scenario (`SPILL_TEST3_001`) is blocked and must never have candidates inserted.
- All scoring functions are pure Python; database access is isolated to `candidate_persistence.py` and `candidate_retrieval.py`.

## Module overview

- `candidate_scoring.py`: Core scoring logic, evidence builder, and summary.
- `candidate_config.py`: Scoring version and feature descriptions.
- `candidate_validation.py`: Score validation rules.
- `candidate_pipeline.py`: End‑to‑end scoring + validation + audit logging.
- `candidate_entry.py`: Single entry point for preparing a candidate for possible persistence.
- `candidate_persistence.py`: Safe persistence (blocked for non‑compatible scenarios).
- `candidate_retrieval.py`: Read candidates from the database.
- `candidate_ranking.py`: Sort candidates by rank.
- `candidate_report.py`: Human‑readable candidate report.
- `candidate_audit.py`: JSONL audit log for candidate actions.
- `candidate_compatibility.py`: Compatibility gate for persistence.
- `candidate_docs.py`: Markdown documentation generator.
- `candidate_health.py`: Health check for scoring components.
- `candidate_cli.py`: CLI helpers for docs and health.

## Safe usage

- Use `prepare_candidate_for_persistence()` to score and validate a candidate.
- Check `persistence_allowed` before calling `persist_candidate()`.
- Never manually insert candidate rows for the blocked test scenario.