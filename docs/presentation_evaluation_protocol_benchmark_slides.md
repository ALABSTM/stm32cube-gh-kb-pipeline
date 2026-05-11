# Evaluation Protocol & Benchmark Results - Slides Ready

## Slide 1 - Why Evaluation in this PFE

Title:
- Evaluation Protocols for STM32Cube Support Persona

Message:
- Goal is not only answer quality, but also controlled behavior:
  - less hallucination
  - less out-of-context responses
  - better evidence traceability (issue/PR/commit/file)
- We evaluate both retrieval quality and live chatbot behavior.

Speaker note:
- "Our protocol validates the pipeline before and after KB upload, then monitors production stability with recurring 50Q campaigns."

---

## Slide 2 - 3-Step Evaluation Protocol

1) Benchmark creation
- Manual benchmark sets:
  - 30Q controlled set (issues/files/mixed)
  - 50Q operational set (ST Quality Index style)

2) Offline retrieval tests (TF-IDF)
- Check lexical retrievability before upload.
- Evaluate whether top retrieved chunks/docs are relevant.

3) Live ST platform run
- Upload Excel/CSV test suite.
- Compare expected answer vs persona answer.
- Track returned answer vs generic abstention vs exception.

Sources:
- pipeline/evaluation/test_tfidf_search_issues_v2.py
- pipeline/evaluation/test_tfidf_search_files_v2.py
- datasets/07_delivery/st_ready/run_h7_50q_ab_test.ps1

---

## Slide 3 - Step 1: Benchmark Creation

30Q reference set:
- File: datasets/06_eval_outputs/h7_eval_30q_questions.md
- Split by intent:
  - Q01-Q10: issues-centric
  - Q11-Q20: files-centric
  - Q21-Q30: mixed issues+files

50Q reference set:
- File: datasets/07_delivery/st_ready/h7_test_suite_excel_ready.csv
- Real support-like coverage:
  - DMA, UART, I2C, USB, ADC, FDCAN, Ethernet, CRYP
  - dual-core, cache/MPU, RTOS, uncertainty handling, evidence policy

Key point:
- Questions are manually authored to avoid synthetic benchmark bias.

---

## Slide 4 - Step 2: Offline TF-IDF Protocol

What is implemented:
- Vectorization with TfidfVectorizer.
- Similarity with cosine similarity.
- Search over valid docs only (is_valid=true).
- Top-k inspection for relevance.

Similarity linking between issues:
- File: pipeline/similarity/compute_issue_similarity_v2.py
- Current code uses:
  - top_k = 3
  - min_sim = 0.40

Important clarification for presentation:
- If you present threshold 0.30, position it as a candidate tuning scenario.
- Current repository truth is 0.40 in active script.

---

## Slide 5 - Step 3: Live ST Quality Index Run

Execution flow:
- Test suite CSV (Question, Expected answer, Tags).
- Script sends each question to persona API.
- Raw outputs stored to datasets/06_eval_outputs/run50_*.csv.

Automation:
- datasets/07_delivery/st_ready/run_h7_50q_ab_test.ps1
- pipeline_Automation/Chat_With_Persona_KB.py

Per question captured fields:
- QID, Question, GoldAnswer, Tags
- AssistantAnswer, Mode, ExitCode

Operational metrics:
- Answer returned
- Generic answer (I DO NOT KNOW / low confidence template)
- Exception (runner/API failure)

---

## Slide 6 - Benchmark Results (30Q A/B)

Source:
- datasets/06_eval_outputs/h7_eval_30q_scored_summary.csv

Global score (/7):
- A (issues_only): 2.93
- B (issues_plus_files): 5.33
- Gain: +2.40 points (~+81.9% relative)

By block:
- Issues block: 6.70 -> 6.20 (slight regression)
- Files block: 1.20 -> 6.00 (major gain)
- Mixed block: 1.30 -> 4.10 (strong gain)

Interpretation:
- Adding files JSON dramatically reduces missing-context responses on files and mixed prompts.

---

## Slide 7 - Benchmark Results (A/B/C on 10Q)

Source:
- datasets/06_eval_outputs/ab_test_scoring_template_h7_output_scored.csv

Average total (/9):
- A raw_issues_h7: 8.4
- B docs_issues_h7_v2: 8.7 (best)
- C st_ready_issues_h7: 6.9

Observed risk in C:
- One critical miss on Q7 (score 0/9, wrong topic retrieval).
- Some precision drops on Q4/Q5/Q9.

Takeaway:
- ST-ready format is useful for delivery, but needs retrieval hardening and alias anchoring to avoid topic drift.

---

## Slide 8 - 50Q Live Run Snapshot (API, CLI)

Sources:
- datasets/06_eval_outputs/run50_baseline_20260423_163941.csv
- datasets/06_eval_outputs/run50_candidate_20260423_163941.csv
- datasets/06_eval_outputs/run50_classic_20260428_162311.csv

Run quality snapshot:
- Baseline:
  - Exceptions: 20/50 (40%)
  - Generic answers: 16/50 (32%)
  - Informative non-generic non-exception: 14/50 (28%)
- Candidate:
  - Exceptions: 25/50 (50%)
  - Generic answers: 15/50 (30%)
  - Informative: 10/50 (20%)
- Classic:
  - Exceptions: 24/50 (48%)
  - Generic answers: 14/50 (28%)
  - Informative: 12/50 (24%)

Interpretation:
- Main bottleneck is runtime robustness (exceptions), not only retrieval precision.

---

## Slide 9 - Incremental Evaluation Strategy (Anti-Hallucination)

Evaluation ladder (what we measure after each increment):
1. issues only
2. files added
3. issues + files
4. resolver cases added
5. diagnostic cards added
6. drivers/domain extension added

Why incremental:
- Isolate marginal gain of each datasource family.
- Detect when a new source increases noise or hallucination.
- Stop regressions before production rollout.

Upload automation confirms 4 active families in batch:
- issues_json
- files_json
- diagnostic_cards_json
- resolver_cases_json

Source:
- pipeline_Automation/Upload_STReady_New_Batch.ps1

---

## Slide 10 - Recommended KPIs for Next Iterations

Primary KPIs:
- Success rate = non-exception answers / total
- Useful answer rate = informative answers / total
- Generic abstention rate
- Source-grounded score (top1 + relevance + hallucination inverse)

Quality gates before each upload:
- Gate 1: stats scripts
- Gate 2: TF-IDF smoke tests
- Gate 3: schema validation
- Gate 4: 30Q controlled benchmark
- Gate 5: recurring 50Q ST Quality Index

Decision policy:
- Promote only if no severe regression on mixed queries and runtime exception rate trends down.

---

## Backup Slide - Commands (if jury asks "how did you run it?")

```bash
python -m pipeline.evaluation.test_stats_issues_v2
python -m pipeline.evaluation.test_stats_files_v2
python -m pipeline.evaluation.test_tfidf_search_issues_v2
python -m pipeline.evaluation.test_tfidf_search_files_v2
python -m pipeline.evaluation.validate_schemas
```

```powershell
./datasets/07_delivery/st_ready/run_h7_50q_ab_test.ps1
./pipeline_Automation/Upload_STReady_New_Batch.ps1 -RemoteUser your.name@st.com -Operation add
```
