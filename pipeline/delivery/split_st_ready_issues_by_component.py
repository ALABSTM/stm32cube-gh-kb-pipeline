import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.utils.paths import PROJECT_ROOT


DEFAULT_INPUT_ROOT = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "by_series"
DEFAULT_INPUT_PATTERN = "**/issues_json/st_ready_issues_with_images_*_with_alfred_image_text.json"
FALLBACK_INPUT_PATTERNS = [
    "**/issues_json/st_ready_issues_with_images_*.json",
    "**/issues_json/st_ready_issues_*_with_alfred_image_text.json",
    "**/issues_json/st_ready_issues_*.json",
]
DEFAULT_OUTPUT_SUBDIR = "by_component"
UNKNOWN_COMPONENT = "UNCATEGORIZED"
GENERIC_DRIVER_COMPONENTS = {
    "ADC", "CAN", "CEC", "COMP", "CORDIC", "CORTEX", "CRC", "CRS", "CRYP", "DAC",
    "DCACHE", "DCMI", "DELAYBLOCK", "DFSDM", "DMA", "DMAMUX", "DMA2D", "DSI", "DTS",
    "ETH", "EXTI", "FDCAN", "FIREWALL", "FLASH", "FMAC", "FMC", "GFXMMU", "GFXTIM",
    "GPIO", "GPU2D", "GTZC", "HASH", "HRTIM", "HSEM", "HSPI", "I2C", "ICACHE", "IPCC",
    "IRDA", "IWDG", "JPEG", "LCD", "LPGPIO", "LPTIM", "LTDC", "MDF", "MDIOS", "MDMA",
    "MRSUBG", "OSPI", "OPAMP", "OTFDEC", "PKA", "PSSI", "PWR", "QSPI", "RAMCFG", "RAMECC",
    "RCC", "RNG", "RTC", "SAI", "SDMMC", "SMARTCARD", "SPDIFRX", "SPI", "SWPMI", "TIM",
    "TSC", "UART", "UCPD", "USART", "USB", "WWDG", "XSPI",
}
COMPONENT_ALIASES = {
    "ETHERNET": "ETH",
    "USB_OTG": "USB",
    "I2C": "I2C",
    "SPI": "SPI",
    "UART": "UART",
    "TIMERS": "TIM",
    "TIMER": "TIM",
}
AMBIGUOUS_COMPONENTS = {"CAN", "COMP", "TIM"}
COMPONENT_PATTERNS = {
    comp: re.compile(rf"(?<![A-Z0-9_]){re.escape(comp)}(?![A-Z0-9_])")
    for comp in GENERIC_DRIVER_COMPONENTS
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at root for {path}")
    return payload


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_component(raw: Any) -> str:
    value = "" if raw is None else str(raw).strip()
    if not value:
        return UNKNOWN_COMPONENT

    lowered = value.lower()
    if lowered in {"none", "unknown", "other", "n/a", "na", "null"}:
        return UNKNOWN_COMPONENT

    canonical = re.sub(r"[^A-Za-z0-9]+", "_", value.upper()).strip("_")
    canonical = COMPONENT_ALIASES.get(canonical, canonical)
    return canonical or UNKNOWN_COMPONENT


def is_generic_driver_component(component: str) -> bool:
    return component in GENERIC_DRIVER_COMPONENTS


def _normalize_candidate_token(raw: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", (raw or "").upper()).strip("_")
    token = COMPONENT_ALIASES.get(token, token)
    return token


def _extract_context_component(st_ready_text: str) -> str:
    if not st_ready_text:
        return UNKNOWN_COMPONENT
    match = re.search(r"\bcomponent=([^,\n]+)", st_ready_text, flags=re.IGNORECASE)
    if not match:
        return UNKNOWN_COMPONENT
    candidate = normalize_component(match.group(1).strip())
    if is_generic_driver_component(candidate):
        return candidate
    return UNKNOWN_COMPONENT


def _extract_keyword_components(st_ready_text: str) -> list[str]:
    if not st_ready_text:
        return []
    match = re.search(r"^Keywords:\s*(.+)$", st_ready_text, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return []

    found: list[str] = []
    for part in match.group(1).split(","):
        candidate = normalize_component(part.strip())
        if is_generic_driver_component(candidate):
            found.append(candidate)
    return found


def _extract_label_components(issue: dict[str, Any]) -> list[str]:
    labels = issue.get("labels")
    if not isinstance(labels, list):
        return []

    found: list[str] = []
    for label in labels:
        if not isinstance(label, str):
            continue
        candidate = normalize_component(label.strip())
        if is_generic_driver_component(candidate):
            found.append(candidate)
    return found


def _score_components_from_upper_tokens(text: str) -> dict[str, int]:
    scores: dict[str, int] = {}
    if not text:
        return scores

    # Use only UPPERCASE/technical-looking tokens to avoid matching common words like "can".
    tokens = re.findall(r"\b[A-Z][A-Z0-9_\-/]{1,}\b", text)
    for token in tokens:
        candidate = _normalize_candidate_token(token)
        if not is_generic_driver_component(candidate):
            continue
        scores[candidate] = scores.get(candidate, 0) + 1
    return scores


def find_component_in_st_ready_text(issue: dict[str, Any]) -> str:
    text_parts = [
        str(issue.get("issue_title") or ""),
        str(issue.get("st_ready_text") or ""),
    ]
    raw_text = "\n".join(text_parts)
    if not raw_text.strip():
        return UNKNOWN_COMPONENT

    # 1) Structured context line has the highest priority when valid.
    context_component = _extract_context_component(str(issue.get("st_ready_text") or ""))
    if context_component != UNKNOWN_COMPONENT:
        return context_component

    # 2) Keywords and labels are reliable structured hints.
    votes: dict[str, int] = {}
    for candidate in _extract_keyword_components(str(issue.get("st_ready_text") or "")):
        votes[candidate] = votes.get(candidate, 0) + 3
    for candidate in _extract_label_components(issue):
        votes[candidate] = votes.get(candidate, 0) + 2

    # 3) Technical uppercase token evidence from full text.
    token_scores = _score_components_from_upper_tokens(raw_text)
    for candidate, score in token_scores.items():
        votes[candidate] = votes.get(candidate, 0) + score

    if not votes:
        return UNKNOWN_COMPONENT

    sorted_candidates = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))
    best_component, best_score = sorted_candidates[0]

    # Confidence guardrails: avoid weak ambiguous predictions.
    min_score = 3 if best_component in AMBIGUOUS_COMPONENTS else 2
    if best_score < min_score:
        return UNKNOWN_COMPONENT

    # If tie with same score, avoid unstable assignment.
    if len(sorted_candidates) > 1 and sorted_candidates[1][1] == best_score:
        return UNKNOWN_COMPONENT

    return best_component


def get_component_detection(issue: dict[str, Any]) -> tuple[str, str]:
    component_from_field = normalize_component(issue.get("component"))
    if component_from_field != UNKNOWN_COMPONENT and is_generic_driver_component(component_from_field):
        return component_from_field, "component_field"

    component_from_text = find_component_in_st_ready_text(issue)
    if component_from_text != UNKNOWN_COMPONENT:
        return component_from_text, "st_ready_text"

    return UNKNOWN_COMPONENT, "none"


def get_series_tag(issues: list[dict[str, Any]], source_path: Path) -> str:
    if issues:
        first = issues[0]
        mcu_series = str(first.get("mcu_series") or "").strip().upper()
        if mcu_series:
            return re.sub(r"[^A-Z0-9]+", "", mcu_series) or "UNK"

        repo = str(first.get("repo") or "").strip().upper()
        if repo.startswith("STM32CUBE"):
            suffix = repo.replace("STM32CUBE", "", 1)
            suffix = re.sub(r"[^A-Z0-9]+", "", suffix)
            if suffix:
                return suffix

    match = re.search(r"stm32cube([a-z0-9]+)", source_path.as_posix(), flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return "UNK"


def split_payload_by_component(
    source_path: Path,
    output_subdir: str,
    datasource_prefix: str,
    dry_run: bool,
) -> dict[str, Any]:
    payload = load_json_object(source_path)
    issues = payload.get("issues")
    if not isinstance(issues, list):
        raise ValueError(f"Missing 'issues' array in {source_path}")

    issue_objects = [item for item in issues if isinstance(item, dict)]
    series_tag = get_series_tag(issue_objects, source_path)

    grouped: dict[str, list[dict[str, Any]]] = {}
    null_component_issues: list[dict[str, Any]] = []
    detection_trace_rows: list[dict[str, Any]] = []
    detection_source_counts: dict[str, int] = {
        "component_field": 0,
        "st_ready_text": 0,
        "none": 0,
    }
    for issue in issue_objects:
        component, source = get_component_detection(issue)
        detection_source_counts[source] = detection_source_counts.get(source, 0) + 1
        issue_out = dict(issue)
        issue_out["component_original"] = issue.get("component")
        issue_out["detected_component"] = None if component == UNKNOWN_COMPONENT else component
        issue_out["component_detection_source"] = source

        if component != UNKNOWN_COMPONENT:
            # Keep payload consistency: files grouped by a component expose that component value.
            issue_out["component"] = component

        detection_trace_rows.append(
            {
                "id": issue.get("id"),
                "issue_number": issue.get("issue_number"),
                "component_field": issue.get("component"),
                "detected_component": None if component == UNKNOWN_COMPONENT else component,
                "detection_source": source,
            }
        )

        if component == UNKNOWN_COMPONENT:
            null_component_issues.append(issue_out)
            continue
        grouped.setdefault(component, []).append(issue_out)

    out_dir = source_path.parent / output_subdir
    manifest_rows: list[dict[str, Any]] = []

    for component in sorted(grouped.keys()):
        component_issues = grouped[component]
        datasource_name = f"{datasource_prefix}_{series_tag}_{component}"
        file_name = f"st_ready_issues_{series_tag.lower()}_{component.lower()}.json"
        out_file = out_dir / file_name

        out_payload = {
            "issues": component_issues,
        }
        if not dry_run:
            save_json(out_file, out_payload)

        manifest_rows.append(
            {
                "series": series_tag,
                "component": component,
                "datasource_name": datasource_name,
                "issues_count": len(component_issues),
                "output_file": str(out_file),
            }
        )

    if null_component_issues:
        null_file = out_dir / f"st_ready_issues_{series_tag.lower()}.json"
        null_payload = {
            "issues": null_component_issues,
        }
        if not dry_run:
            save_json(null_file, null_payload)

        manifest_rows.append(
            {
                "series": series_tag,
                "component": None,
                "datasource_name": f"{datasource_prefix}_{series_tag}",
                "issues_count": len(null_component_issues),
                "output_file": str(null_file),
            }
        )

    summary = {
        "source_file": str(source_path),
        "output_dir": str(out_dir),
        "created_at": utc_now_iso(),
        "series": series_tag,
        "source_issues_count": len(issue_objects),
        "components_count": len(grouped),
        "null_component_issues_count": len(null_component_issues),
        "detection_source_counts": detection_source_counts,
        "datasources": manifest_rows,
        "dry_run": dry_run,
    }

    summary_file = out_dir / f"summary_by_component_{series_tag.lower()}.json"
    if not dry_run:
        save_json(summary_file, summary)

        trace_file = out_dir / f"component_detection_trace_{series_tag.lower()}.json"
        save_json(
            trace_file,
            {
                "series": series_tag,
                "source_file": str(source_path),
                "rows": detection_trace_rows,
            },
        )

    return summary


def resolve_source_files(input_root: Path, pattern: str) -> list[Path]:
    files = sorted(input_root.glob(pattern))
    if files:
        return files

    fallback_files: list[Path] = []
    for fallback_pattern in FALLBACK_INPUT_PATTERNS:
        fallback_files.extend(sorted(input_root.glob(fallback_pattern)))
    # Preserve deterministic order and remove duplicates.
    return sorted(set(fallback_files))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Split ST-ready issues-with-images payloads into per-component JSON files "
            "for datasource upload (issues_<SERIES>_<COMPONENT>)."
        )
    )
    parser.add_argument("--input-file", type=Path, help="Single source JSON file to split.")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--pattern", default=DEFAULT_INPUT_PATTERN)
    parser.add_argument("--output-subdir", default=DEFAULT_OUTPUT_SUBDIR)
    parser.add_argument("--datasource-prefix", default="issues")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    summaries: list[dict[str, Any]] = []

    if args.input_file:
        source_files = [args.input_file.resolve()]
    else:
        input_root = args.input_root.resolve()
        if not input_root.exists():
            raise FileNotFoundError(f"Input root not found: {input_root}")
        source_files = resolve_source_files(input_root=input_root, pattern=args.pattern)

    if not source_files:
        raise ValueError(
            "No source files found. Expected ST-ready issues-with-images JSON files "
            "(with or without Alfred suffix)."
        )

    for source_path in source_files:
        if not source_path.exists():
            raise FileNotFoundError(f"Input file not found: {source_path}")

        summary = split_payload_by_component(
            source_path=source_path,
            output_subdir=args.output_subdir,
            datasource_prefix=args.datasource_prefix,
            dry_run=args.dry_run,
        )
        summaries.append(summary)
        print(
            "[split_issues_by_component] "
            f"series={summary['series']} components={summary['components_count']} "
            f"issues={summary['source_issues_count']} output={summary['output_dir']}"
        )

    total_components = sum(int(s.get("components_count", 0)) for s in summaries)
    total_issues = sum(int(s.get("source_issues_count", 0)) for s in summaries)
    print(
        "[split_issues_by_component] done "
        f"files={len(summaries)} components={total_components} issues={total_issues}"
    )


if __name__ == "__main__":
    main()
