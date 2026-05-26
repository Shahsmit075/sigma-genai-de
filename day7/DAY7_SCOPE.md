# Day 7 — Pipeline Brain: Scope & Flow

> **Overall Goal**: AI-assisted, spec-driven pipeline delivery — from a plain-English spec to a production-ready PySpark pipeline + Airflow DAG in ~45 minutes.

---

## Overall Goal

- Learn to use AI (Amazon Bedrock / Nova) as a data engineering accelerator
- Understand WHERE AI adds value vs. WHERE human review is mandatory
- Produce real, reviewable pipeline artifacts that feed Day 8 (tests) and Day 12 (self-heal)

---

## Activity Flow

```
[M0: Write Spec] → [M1: Generate Pipeline] → [M2: Generate DAG] → [M3: Harden Pipeline] → [M5: Code Review]
                                                                          ↑
                                                               [M4: Schema Drift] (standalone stretch)
```

---

## Activity-Wise Goals

### Module 0 — Write Your Team Spec *(~30 min)*
- **What**: Each team picks their assigned scenario (Team 1–9) from `0_team_spec_scenarios.md`
- **Do**: Fill in all 6 sections of the spec template → save as `lab/my_pipeline_spec.txt`
- **Why**: M1 auto-detects this file; your output will be unique per team
- **Deliverable**: `lab/my_pipeline_spec.txt`

---

### Module 1 — Spec → PySpark Pipeline *(~10 min)*
- **What**: AI generates a full Bronze → Silver → Gold PySpark pipeline from your spec
- **How**: Two-phase Bedrock call (Nova Lite) — Phase 1: Bronze+Silver, Phase 2: Gold aggregations
- **Manual First**: Write down the 3 PySpark transforms you'd need for Silver *before* running
- **Read debrief**: AI gets structure right; gets broadcast hints, hardcoded paths, idempotency wrong
- **Deliverables**:
  - `pipeline_brain/generated_pipeline.py` — the PySpark code
  - `pipeline_brain/generation_report.json` — model + token metadata

---

### Module 2 — Pipeline → Airflow DAG *(~10 min)*
- **What**: AI generates a production Airflow DAG (tasks, retry logic, SLA, failure callbacks)
- **How**: Single Bedrock call (Nova Lite) — DAG structure is formulaic
- **Manual First**: Draw a box-and-arrow DAG on paper *before* running
- **Read debrief**: AI nails structure + dependencies; SLA values, operator choice (EMR vs Python), and alert routing are your decisions
- **Deliverables**:
  - `pipeline_brain/sigma_dag.py` — Airflow DAG
  - `pipeline_brain/dag_report.json` — task count + dependency metadata

---

### Module 3 — Pipeline Hardening *(~10 min)*
- **What**: AI (Nova Pro) takes generated pipeline and adds 5 production-safety patterns
- **5 Things Added**:
  1. `try/except` with re-raise around each stage
  2. Idempotency — delete-partition-then-write (not just `mode=overwrite`)
  3. Partition pruning on all reads
  4. Row count logging at every stage
  5. `run_metadata_{date}.json` output (read by Day 12 self-heal agent)
- **Manual First**: Find one silent failure point in `generated_pipeline.py` *before* running
- **Deliverables**:
  - `pipeline_brain/hardened_pipeline.py`
  - `pipeline_brain/hardening_report.json`

---

### Module 4 — Schema Drift (Stretch Goal) *(~30 min, standalone)*
- **What**: Simulate upstream schema change (2 new columns appear without warning), then AI generates a handler
- **Scenario**: `payment_gateway` (string) + `discount_amount` (float) appear silently in CSV
- **Manual First**: Decide — add / drop / flag / halt? — *before* running
- **Student Task**: Add `"refund_flag": "boolean"` to `DRIFTED_COLUMNS` → re-run → observe AI response
- **Deliverables**:
  - `pipeline_brain/schema_drift_report.json`
  - `pipeline_brain/schema_evolution_handler.py`

---

### Module 5 — Code Review Agent *(~45 min)*
- **What**: AI (Nova Pro) runs a 12-point engineering checklist on `generated_pipeline.py`
- **12 Checkpoints**: Idempotency, Error Handling, Partition Pruning, Row Count Logging, Business Rules, NULL Handling, Broadcast Hint, Hardcoded Paths, Schema Validation, Deduplication, Metadata Output, Imports
- **Manual First**: Read `generated_pipeline.py` for 5 min; write 1 thing wrong + 1 thing to change
- **Student Task**: Fix ≥2 FAIL items → save as `fixed_pipeline.py` + document in `my_review_notes.txt`
- **Deliverables**:
  - `pipeline_brain/code_review.json` *(required)*
  - `pipeline_brain/fixed_pipeline.py` *(bonus)*
  - `pipeline_brain/my_review_notes.txt` *(bonus)*

---

## Validate & Push

```bash
cd day7
python tests/validate_day7.py   # All green → push
git add .
git commit -m "Day 7 done"
git push
```

**Validator checks**: file existence, size, valid JSON, correct keys, Nova Pro was used for M3

---

## Platform Connection

| Day | Theme | Dependency |
|-----|-------|------------|
| **Day 7** | Pipeline Brain | YOU ARE HERE |
| Day 8 | DevOps Brain | Tests for `hardened_pipeline.py`; CI validates DAG syntax on every PR |
| Day 11 | Governance Agent | Monitors DAG runs; quarantines bad data using same schema drift logic |
| Day 12 | Self-Heal Agent | Reads `run_metadata.json` from today's pipeline to detect anomalies |
