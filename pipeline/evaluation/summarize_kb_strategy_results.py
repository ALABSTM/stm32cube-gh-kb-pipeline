import argparse
import csv
from collections import defaultdict
from pathlib import Path

INPUT_PATH = Path("docs/evaluation/kb_strategy_comparison_template.csv")

# Weighted score emphasizing answer correctness and retrieval quality
W_TOP1 = 0.40
W_TOP3 = 0.20
W_ANSWER = 0.35
W_HALLUCINATION = -0.15
W_LATENCY = -0.05  # normalized inverse contribution


def to_int(value: str) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def to_float(value: str) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return 0.0


def is_evaluated_row(row: dict) -> bool:
    required = [
        row.get("has_relevant_doc_top1", ""),
        row.get("has_relevant_doc_top3", ""),
        row.get("final_answer_correct", ""),
        row.get("hallucination", ""),
        row.get("latency_seconds", ""),
    ]
    return all(str(v).strip() != "" for v in required)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize KB strategy comparison CSV.")
    parser.add_argument("--input", default=str(INPUT_PATH), help="Path to comparison CSV")
    parser.add_argument("--run-id", default="", help="Optional run_id filter (e.g. R0)")
    parser.add_argument("--strategy", default="", help="Optional strategy_id filter")
    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}")

    rows = []
    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if args.run_id and (row.get("run_id", "").strip() != args.run_id):
                continue
            if args.strategy and (row.get("strategy_id", "").strip() != args.strategy):
                continue
            if is_evaluated_row(row):
                rows.append(row)

    if not rows:
        print("No evaluated rows found for selected filters.")
        return

    by_strategy = defaultdict(list)
    for row in rows:
        sid = (row.get("strategy_id") or "").strip()
        if sid:
            by_strategy[sid].append(row)

    if not by_strategy:
        print("No strategy rows found.")
        return

    # For latency normalization
    all_latencies = [to_float(r.get("latency_seconds", "0")) for r in rows if (r.get("latency_seconds") or "").strip()]
    min_lat = min(all_latencies) if all_latencies else 0.0
    max_lat = max(all_latencies) if all_latencies else 1.0
    lat_range = max(max_lat - min_lat, 1e-9)

    summary = []
    for sid, srows in by_strategy.items():
        n = len(srows)
        top1 = sum(to_int(r.get("has_relevant_doc_top1", "0")) for r in srows) / n
        top3 = sum(to_int(r.get("has_relevant_doc_top3", "0")) for r in srows) / n
        ans = sum(to_int(r.get("final_answer_correct", "0")) for r in srows) / n
        hal = sum(to_int(r.get("hallucination", "0")) for r in srows) / n

        lat_values = [to_float(r.get("latency_seconds", "0")) for r in srows if (r.get("latency_seconds") or "").strip()]
        avg_lat = sum(lat_values) / len(lat_values) if lat_values else 0.0

        # Lower latency should increase score, so invert normalized latency
        lat_norm = (avg_lat - min_lat) / lat_range if all_latencies else 0.0
        lat_bonus = 1.0 - lat_norm

        score = (
            W_TOP1 * top1
            + W_TOP3 * top3
            + W_ANSWER * ans
            + W_HALLUCINATION * hal
            + W_LATENCY * (1.0 - lat_bonus)
        )

        summary.append(
            {
                "strategy_id": sid,
                "n_queries": n,
                "top1_rate": round(top1, 4),
                "top3_rate": round(top3, 4),
                "answer_rate": round(ans, 4),
                "hallucination_rate": round(hal, 4),
                "avg_latency_s": round(avg_lat, 3),
                "score": round(score, 4),
            }
        )

    summary.sort(key=lambda x: x["score"], reverse=True)

    print("\n=== KB Strategy Comparison Summary ===")
    print("strategy_id,n_queries,top1_rate,top3_rate,answer_rate,hallucination_rate,avg_latency_s,score")
    for s in summary:
        print(
            f"{s['strategy_id']},{s['n_queries']},{s['top1_rate']},{s['top3_rate']},"
            f"{s['answer_rate']},{s['hallucination_rate']},{s['avg_latency_s']},{s['score']}"
        )

    best = summary[0]
    print(f"\nRecommended strategy: {best['strategy_id']} (score={best['score']})")


if __name__ == "__main__":
    main()
