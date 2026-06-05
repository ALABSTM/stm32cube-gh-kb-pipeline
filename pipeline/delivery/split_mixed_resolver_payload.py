import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object at root.")
    return payload


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sanitize_resolver_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        cleaned = dict(card)
        cleaned["rootTagPath"] = "resolver_cases"
        out.append(cleaned)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Split a mixed ST-ready resolver JSON into separate resolver_cases and "
            "diagnostic_cards files for distinct datasource uploads."
        )
    )
    parser.add_argument("--input", required=True, help="Path to mixed JSON payload.")
    parser.add_argument("--resolver-output", required=True, help="Output JSON path for resolver_cases root.")
    parser.add_argument("--diagnostic-output", required=True, help="Output JSON path for diagnostic_cards root.")
    args = parser.parse_args()

    in_path = Path(args.input)
    payload = load_json(in_path)

    resolver_cards = payload.get("resolver_cases") if isinstance(payload.get("resolver_cases"), list) else []
    diagnostic_cards = payload.get("diagnostic_cards") if isinstance(payload.get("diagnostic_cards"), list) else []

    resolver_payload = {"resolver_cases": sanitize_resolver_cards(resolver_cards)}
    diagnostic_payload = {"diagnostic_cards": diagnostic_cards}

    save_json(Path(args.resolver_output), resolver_payload)
    save_json(Path(args.diagnostic_output), diagnostic_payload)

    print(
        "[split_mixed_resolver_payload] "
        f"resolver_cases={len(resolver_payload['resolver_cases'])}, "
        f"diagnostic_cards={len(diagnostic_payload['diagnostic_cards'])}"
    )


if __name__ == "__main__":
    main()