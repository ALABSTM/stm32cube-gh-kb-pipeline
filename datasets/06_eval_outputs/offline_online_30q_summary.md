# Offline vs Online 30Q Summary

This summary is prefilled from the existing offline benchmark (A vs B) and normalized to /100.
Online ST Quality Index columns are intentionally left blank until online scores are exported.

| scope | run_id | dataset_label | offline_avg_total_0_to_7 | offline_avg_0_to_100 | online_avg_0_to_100 | delta_online_minus_offline_points | notes |
|---|---|---|---:|---:|---:|---:|---|
| global | A | issues_only | 2.93 | 41.86 |  |  | online not filled yet |
| global | B | issues_plus_files | 5.33 | 76.14 |  |  | online not filled yet |
| issues | A | issues_only | 6.70 | 95.71 |  |  | online not filled yet |
| issues | B | issues_plus_files | 6.20 | 88.57 |  |  | online not filled yet |
| files | A | issues_only | 1.20 | 17.14 |  |  | online not filled yet |
| files | B | issues_plus_files | 6.00 | 85.71 |  |  | online not filled yet |
| mixed | A | issues_only | 1.30 | 18.57 |  |  | online not filled yet |
| mixed | B | issues_plus_files | 4.10 | 58.57 |  |  | online not filled yet |
| global | A->B | issues_only->issues_plus_files | 2.40 | 34.28 |  |  | positive means B better than A |
| issues | A->B | issues_only->issues_plus_files | -0.50 | -7.14 |  |  | positive means B better than A |
| files | A->B | issues_only->issues_plus_files | 4.80 | 68.57 |  |  | positive means B better than A |
| mixed | A->B | issues_only->issues_plus_files | 2.80 | 40.00 |  |  | positive means B better than A |

## How to complete online columns

1. Fill quality_index_30q_online_scores_template.csv with online scores (/100) from ST Quality Index.
2. Run:

python -m pipeline.evaluation.compare_offline_online_quality

3. Read refreshed outputs:
- offline_online_30q_summary.csv
- offline_online_30q_summary.md
