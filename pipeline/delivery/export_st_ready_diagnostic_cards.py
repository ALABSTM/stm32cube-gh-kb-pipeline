import argparse
import json
import re
from pathlib import Path
from typing import Any

from shared.utils.paths import PROJECT_ROOT, get_config_path




def load_config() -> dict[str, Any]:
    return json.loads(get_config_path().read_text(encoding="utf-8"))


def normalize_whitespace(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def first_sentence(text: str | None, max_chars: int = 260) -> str:
    normalized = normalize_whitespace(text)
    if not normalized:
        return ""
    match = re.search(r"[.!?]", normalized)
    if match and match.end() <= max_chars:
        return normalized[: match.end()].strip()
    return normalized[:max_chars].strip()


def looks_like_conversational_noise(text: str | None) -> bool:
    value = normalize_whitespace(text).lower()
    if not value:
        return True
    noise_prefixes = [
        "hi @",
        "hello @",
        "thank you",
        "thanks",
        "best regards",
        "with regards",
        "st internal reference",
    ]
    return any(value.startswith(prefix) for prefix in noise_prefixes)


def clean_signal_sentence(text: str | None, max_chars: int = 260) -> str:
    sentence = first_sentence(text, max_chars=max_chars)
    if looks_like_conversational_noise(sentence):
        return ""
    return sentence


def extract_issue_body(st_ready_text: str | None) -> str:
    text = st_ready_text or ""
    marker = "\n\nTechnical details:\n"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    alt_marker = "\nTechnical details:\n"
    if alt_marker in text:
        return text.split(alt_marker, 1)[1].strip()
    return text.strip()


def slugify(value: str, max_len: int = 80) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if not text:
        return "untitled"
    return text[:max_len].strip("-")


def load_json_array(path: Path, preferred_key: str | None = None) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if preferred_key and isinstance(payload.get(preferred_key), list):
            return [item for item in payload.get(preferred_key, []) if isinstance(item, dict)]
        for value in payload.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError(f"Unsupported JSON root in {path}")


def parse_prefixed_lines(text: str | None, prefixes: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        if key in prefixes:
            out[key] = value.strip()
    return out


def split_keywords(raw_keywords: str | None) -> list[str]:
    if not raw_keywords:
        return []
    items = [normalize_whitespace(item) for item in str(raw_keywords).split(",")]
    return [item for item in items if item]


def normalize_series(value: str | None) -> str | None:
    series = normalize_whitespace(value)
    if not series:
        return None
    upper = series.upper()
    if upper.startswith("STM32"):
        return upper
    if re.fullmatch(r"[A-Z]\d+", upper):
        return f"STM32{upper}"
    return upper


def infer_target_series(repo: str, issue_doc: dict[str, Any] | None) -> list[str]:
    if issue_doc:
        normalized = normalize_series(str(issue_doc.get("mcu_series") or ""))
        if normalized:
            return [normalized]
    repo_upper = repo.upper()
    match = re.search(r"(H\d+|F\d+|L\d+|G\d+|U\d+|WB\d+|WL\d+|MP\d+)", repo_upper)
    if match:
        return [f"STM32{match.group(1)}"]
    return []


def extract_api_family_tags(*texts: str) -> list[str]:
    anchor_re = re.compile(r"\b(?:HAL|LL|BSP|MX|CMSIS)_[A-Za-z0-9_]+\b")
    tags: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in anchor_re.findall(text or ""):
            if match.lower() in seen:
                continue
            seen.add(match.lower())
            tags.append(match)
            if len(tags) >= 8:
                return tags
    return tags


def build_pattern_tags(*texts: str) -> list[str]:
    joined = " ".join(texts).lower()
    patterns = [
        (r"callback", "callback_not_reached"),
        (r"busy", "state_stuck_busy"),
        (r"timeout|timed out", "timeout"),
        (r"block|blocking", "blocking_behavior"),
        (r"dma", "dma_path"),
        (r"compile|build", "compile_error"),
        (r"crash|hardfault|fault", "crash_fault"),
        (r"regression|upgrade|version", "version_regression"),
        (r"clock", "clocking"),
        (r"pin|gpio|mux", "pinmux"),
        (r"irq|interrupt", "interrupt_path"),
        (r"cache|mpu", "cache_dma"),
    ]
    out: list[str] = []
    for pattern, tag in patterns:
        if re.search(pattern, joined) and tag not in out:
            out.append(tag)
    return out[:8]


def build_query_aliases(issue_doc: dict[str, Any] | None, pattern_tags: list[str], api_tags: list[str]) -> list[str]:
    aliases: list[str] = []
    issue_text = (issue_doc or {}).get("st_ready_text") or ""
    body = extract_issue_body(issue_text)
    low = body.lower()
    has_spi_dma = any(tag.startswith("HAL_SPI") for tag in api_tags) and "dma_path" in pattern_tags
    has_blocking_like_pattern = "state_stuck_busy" in pattern_tags or "callback_not_reached" in pattern_tags

    if has_spi_dma:
        aliases.append("HAL_SPI_Transmit_DMA")
        aliases.append("SPI DMA transfer")

    # Prioritize lexical anchors that users ask with in natural language.
    if has_spi_dma and has_blocking_like_pattern:
        aliases.append("HAL_SPI_Transmit_DMA blocking function")
        aliases.append("small amount of data")
        aliases.append("small transfer")
        aliases.append("2 bytes")
        aliases.append("2 bytes example")

    if has_blocking_like_pattern and ("dma_path" in pattern_tags or has_spi_dma):
        aliases.append("blocking function")
        aliases.append("seems blocking")
        aliases.append("blocking behavior")
        aliases.append("callback not reached")
        aliases.append("state stuck busy")

    if re.search(r"\bsmall\b", low) and re.search(r"\btransfer\b", low):
        aliases.append("small transfer")

    if re.search(r"\btiny\b", low) and re.search(r"\btransfer\b", low):
        aliases.append("tiny transfer")

    size_matches = re.findall(r"\b(\d{1,4})\s*bytes?\b", low)
    for size in size_matches[:3]:
        aliases.append(f"{size} bytes")

    return dedupe(aliases, limit=12)


def dedupe(items: list[str], limit: int = 12) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = normalize_whitespace(item)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
        if len(out) >= limit:
            break
    return out


def ensure_list(items: list[str], fallback: str) -> list[str]:
    cleaned = dedupe(items)
    return cleaned if cleaned else [fallback]


def build_debug_checks(
    issue_doc: dict[str, Any] | None,
    resolver_doc: dict[str, Any] | None,
    pattern_tags: list[str],
) -> list[str]:
    checks: list[str] = []
    if "callback_not_reached" in pattern_tags or "state_stuck_busy" in pattern_tags:
        checks.extend(
            [
                "Instrument callback entry points and verify state transitions around the failing call",
                "Check whether the peripheral state returns to READY after the operation",
            ]
        )
    if "compile_error" in pattern_tags:
        checks.append("Rebuild with the exact toolchain and package version referenced in the report")
    if "timeout" in pattern_tags:
        checks.append("Capture timeout path timing and compare it with clock and interrupt configuration")
    if resolver_doc and resolver_doc.get("linked_file_paths"):
        first_path = resolver_doc.get("linked_file_paths")[0]
        checks.append(f"Review the linked fix path and compare your local source against {first_path}")
    component = normalize_whitespace((issue_doc or {}).get("component") or "")
    if component:
        checks.append(f"Validate the exact {component} configuration on the target board and firmware package")
    checks.append("Reproduce on a minimal project using the same board, Cube package, and middleware settings")
    return dedupe(checks, limit=5)


def build_workarounds(
    issue_fields: dict[str, str],
    resolver_fields: dict[str, str],
    pattern_tags: list[str],
) -> list[str]:
    workarounds: list[str] = []
    fix_hint = clean_signal_sentence(issue_fields.get("Fix"), max_chars=220)
    if fix_hint:
        workarounds.append(fix_hint)
    if resolver_fields.get("Candidate PRs"):
        workarounds.append("Test the candidate fix path or PR on an isolated branch before merging locally")
    if "dma_path" in pattern_tags:
        workarounds.append("Try an alternate transfer mode on a minimal case to isolate DMA-specific behavior")
    workarounds.append("Pin a known-good firmware package version while validating the issue scope")
    return dedupe(workarounds, limit=4)


def build_confirmed_facts(
    issue_doc: dict[str, Any] | None,
    resolver_doc: dict[str, Any] | None,
    issue_fields: dict[str, str],
) -> list[str]:
    facts: list[str] = []
    if issue_doc and issue_doc.get("github_url"):
        facts.append(f"Issue evidence exists in {issue_doc.get('repo')} issue #{issue_doc.get('issue_number')}")
    if issue_doc and issue_doc.get("rescue_applied"):
        facts.append("The issue was rescued by the preprocessing filter because technical signals were detected")
    evidence_strength = normalize_whitespace((issue_doc or {}).get("evidence_strength") or "")
    if evidence_strength:
        facts.append(f"Issue evidence strength is rated {evidence_strength}")
    if resolver_doc and resolver_doc.get("resolution_status"):
        facts.append(
            "Resolver linkage status is "
            f"{resolver_doc.get('resolution_status')} with confidence {resolver_doc.get('link_confidence') or 'unknown'}"
        )
    if resolver_doc and resolver_doc.get("linked_commit_shas"):
        facts.append("A linked commit or pull request exists for this issue path")
    root_cause = clean_signal_sentence(issue_fields.get("Root cause"), max_chars=180)
    if root_cause:
        facts.append(root_cause)
    return dedupe(facts, limit=4)


def build_constraints(
    issue_fields: dict[str, str],
    issue_doc: dict[str, Any] | None,
    resolver_doc: dict[str, Any] | None,
) -> list[str]:
    constraints: list[str] = []
    issue_constraint = first_sentence(issue_fields.get("Constraints"), max_chars=220)
    if issue_constraint:
        constraints.append(issue_constraint)
    if issue_doc and issue_doc.get("rescue_applied"):
        constraints.append("This card is derived from a rescued issue and still requires board-level validation")
    if resolver_doc and resolver_doc.get("link_confidence") in {"low", "medium"}:
        constraints.append("Linked fix evidence is not strong enough to assume universal applicability")
    constraints.append("Validate against the exact MCU series, board, package version, and local integration path")
    return dedupe(constraints, limit=4)


def build_plausible_diagnosis(
    issue_doc: dict[str, Any] | None,
    resolver_doc: dict[str, Any] | None,
    pattern_tags: list[str],
) -> list[str]:
    out: list[str] = []
    if issue_doc:
        layer = normalize_whitespace(issue_doc.get("layer") or "")
        component = normalize_whitespace(issue_doc.get("component") or "")
        issue_kind = normalize_whitespace(issue_doc.get("issue_kind") or "")
        if layer or component or issue_kind:
            out.append(
                "Observed behavior aligns with "
                f"{', '.join([x for x in [layer, component, issue_kind] if x])} issue characteristics"
            )
    if resolver_doc and resolver_doc.get("resolution_status") == "merged_fix":
        out.append("A mainline fix likely exists, so local package drift is a plausible cause")
    elif resolver_doc and resolver_doc.get("resolution_status") == "candidate_fix":
        out.append("A candidate fix exists, suggesting the problem may already be understood upstream")
    if "version_regression" in pattern_tags:
        out.append("Behavior may depend on the exact Cube or HAL version in use")
    if "blocking_behavior" in pattern_tags or "state_stuck_busy" in pattern_tags:
        out.append("The application may be observing a completion-path or state-machine defect rather than a true hard block")
    return ensure_list(out, "The issue requires targeted reproduction to distinguish configuration error from upstream defect")


def build_likely_causes(issue_fields: dict[str, str], resolver_fields: dict[str, str]) -> list[str]:
    causes: list[str] = []
    root_cause = clean_signal_sentence(issue_fields.get("Root cause"), max_chars=220)
    if root_cause:
        causes.append(root_cause)
    assessment = clean_signal_sentence(resolver_fields.get("Assessment"), max_chars=220)
    if assessment:
        causes.append(assessment)
    resolver_signal = clean_signal_sentence(resolver_fields.get("Resolver signal"), max_chars=220)
    if resolver_signal:
        causes.append(resolver_signal)
    return ensure_list(causes, "Root cause is not explicit; use the issue thread and linked changes for triage")


def build_evidence_refs(issue_doc: dict[str, Any] | None, resolver_doc: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if issue_doc and issue_doc.get("github_url"):
        refs.append(
            {
                "type": "issue",
                "id": issue_doc.get("issue_number"),
                "url": issue_doc.get("github_url"),
                "confidence": issue_doc.get("evidence_strength"),
            }
        )
    if resolver_doc:
        for url in resolver_doc.get("linked_pr_urls") or []:
            refs.append({"type": "pull_request", "url": url, "confidence": resolver_doc.get("link_confidence")})
        for url in resolver_doc.get("linked_commit_urls") or []:
            refs.append({"type": "commit", "url": url, "confidence": resolver_doc.get("link_confidence")})
    return refs[:6]


def build_keywords(
    issue_doc: dict[str, Any] | None,
    resolver_doc: dict[str, Any] | None,
    issue_fields: dict[str, str],
    api_tags: list[str],
) -> list[str]:
    keywords: list[str] = []
    if issue_doc:
        keywords.extend(split_keywords(issue_fields.get("Keywords")))
        keywords.extend(issue_doc.get("labels") or [])
        for key in ["component", "layer", "issue_kind", "severity", "board"]:
            value = normalize_whitespace(issue_doc.get(key) or "")
            if value and value.lower() not in {"none", "unknown", "other", "n/a"}:
                keywords.append(value)
    if resolver_doc:
        keywords.extend(resolver_doc.get("impacted_modules") or [])
        keywords.extend(resolver_doc.get("impacted_components") or [])
        status = normalize_whitespace(resolver_doc.get("resolution_status") or "")
        if status:
            keywords.append(status)
    keywords.extend(api_tags)
    return dedupe(keywords, limit=14)


def build_st_ready_text(card: dict[str, Any]) -> str:
    evidence_links = [ref.get("url") for ref in card.get("evidence_refs") or [] if ref.get("url")]
    lines = [
        f"Problem: {card.get('title')}",
        f"Context: repo={card.get('repo')}, issue_number={card.get('issue_number')}, target_series={', '.join(card.get('target_series') or []) or 'unknown'}, source_types={', '.join(card.get('source_types') or [])}",
        f"Symptoms: {card.get('symptom_summary')}",
        f"Query aliases: {' | '.join(card.get('query_aliases') or [])}",
        f"Likely causes: {' | '.join(card.get('likely_causes') or [])}",
        f"Confirmed facts: {' | '.join(card.get('confirmed_facts') or [])}",
        f"Plausible diagnosis: {' | '.join(card.get('plausible_diagnosis') or [])}",
        f"Debug actions: {' | '.join(card.get('debug_checks') or [])}",
        f"Workaround: {' | '.join(card.get('possible_workarounds') or [])}",
        f"Constraints: {' | '.join(card.get('constraints_or_limits') or [])}",
        f"Evidence links: {' | '.join(evidence_links)}",
        f"Keywords: {' '.join(card.get('keywords') or [])}",
    ]
    return "\n".join(lines).strip()


def build_diagnostic_card(
    repo: str,
    issue_doc: dict[str, Any] | None,
    resolver_doc: dict[str, Any] | None,
) -> dict[str, Any]:
    issue_fields = parse_prefixed_lines(
        (issue_doc or {}).get("st_ready_text"),
        {"Problem", "Context", "Root cause", "Fix", "Constraints", "Keywords"},
    )
    resolver_fields = parse_prefixed_lines(
        (resolver_doc or {}).get("resolver_card_text"),
        {"Problem", "Context", "Resolver signal", "Assessment", "Candidate PRs", "Commit evidence", "Constraints"},
    )

    title = normalize_whitespace(
        (issue_doc or {}).get("issue_title")
        or (resolver_doc or {}).get("issue_title")
        or issue_fields.get("Problem")
        or resolver_fields.get("Problem")
        or "Untitled diagnostic case"
    )
    issue_number = (issue_doc or {}).get("issue_number") or (resolver_doc or {}).get("issue_number")
    api_tags = extract_api_family_tags(
        (issue_doc or {}).get("st_ready_text") or "",
        (resolver_doc or {}).get("resolver_card_text") or "",
    )
    issue_body = extract_issue_body((issue_doc or {}).get("st_ready_text"))
    pattern_tags = build_pattern_tags(
        title,
        issue_fields.get("Root cause", ""),
        issue_fields.get("Fix", ""),
        issue_body,
        (issue_doc or {}).get("st_ready_text") or "",
        (resolver_doc or {}).get("resolver_card_text") or "",
    )
    query_aliases = build_query_aliases(issue_doc, pattern_tags, api_tags)
    symptom_summary = clean_signal_sentence(issue_fields.get("Fix"), max_chars=220)
    if not symptom_summary:
        symptom_summary = clean_signal_sentence(title, max_chars=220) or title
    if query_aliases and not any(alias.lower() in symptom_summary.lower() for alias in query_aliases[:2]):
        symptom_summary = f"{symptom_summary} ({', '.join(query_aliases[:2])})."
    affected_context = first_sentence(issue_fields.get("Context") or resolver_fields.get("Context"), max_chars=220)
    likely_causes = build_likely_causes(issue_fields, resolver_fields)
    confirmed_facts = build_confirmed_facts(issue_doc, resolver_doc, issue_fields)
    plausible_diagnosis = build_plausible_diagnosis(issue_doc, resolver_doc, pattern_tags)
    debug_checks = build_debug_checks(issue_doc, resolver_doc, pattern_tags)
    possible_workarounds = build_workarounds(issue_fields, resolver_fields, pattern_tags)
    constraints = build_constraints(issue_fields, issue_doc, resolver_doc)
    evidence_refs = build_evidence_refs(issue_doc, resolver_doc)
    keywords = build_keywords(issue_doc, resolver_doc, issue_fields, api_tags)
    keywords = dedupe(query_aliases + keywords, limit=24)
    component = normalize_whitespace((issue_doc or {}).get("component") or "")
    peripheral_tags = dedupe([component] if component else [], limit=4)
    source_types = [
        source
        for source, doc in [("rescued_issue", issue_doc if (issue_doc or {}).get("rescue_applied") else None), ("resolver_case", resolver_doc)]
        if doc is not None
    ]
    if not source_types and issue_doc:
        source_types = ["issue"]

    card = {
        "id": f"diag::{repo}::issue::{issue_number or slugify(title)}",
        "card_id": f"diag_{repo.lower()}_{issue_number or slugify(title)}",
        "rootTagPath": "diagnostic_cards",
        "delivery_template": "st_v1_diagnostic_card",
        "repo_scope": repo,
        "repo": repo,
        "title": title,
        "label": title,
        "externalURL": (issue_doc or {}).get("github_url") or (resolver_doc or {}).get("issue_url"),
        "issue_number": issue_number,
        "issue_title": (issue_doc or {}).get("issue_title") or (resolver_doc or {}).get("issue_title"),
        "issue_state": (issue_doc or {}).get("state") or (resolver_doc or {}).get("issue_state"),
        "issue_kind": (issue_doc or {}).get("issue_kind"),
        "severity": (issue_doc or {}).get("severity"),
        "component": (issue_doc or {}).get("component"),
        "board": (issue_doc or {}).get("board"),
        "target_series": infer_target_series(repo, issue_doc),
        "category": "technical_diagnosis",
        "source_types": source_types,
        "evidence_strength": (issue_doc or {}).get("evidence_strength") or (resolver_doc or {}).get("link_confidence"),
        "rescue_applied": bool((issue_doc or {}).get("rescue_applied")),
        "resolution_status": (resolver_doc or {}).get("resolution_status"),
        "peripheral_tags": peripheral_tags,
        "technical_pattern_tags": pattern_tags,
        "api_family_tags": api_tags,
        "query_aliases": query_aliases,
        "symptom_summary": symptom_summary,
        "affected_context": affected_context,
        "likely_causes": likely_causes,
        "confirmed_facts": confirmed_facts,
        "plausible_diagnosis": plausible_diagnosis,
        "debug_checks": debug_checks,
        "possible_workarounds": possible_workarounds,
        "constraints_or_limits": constraints,
        "evidence_refs": evidence_refs,
        "keywords": keywords,
    }
    card["st_ready_text"] = build_st_ready_text(card)
    return card


def export_repo_json(repo: str, include_all_issues: bool = False) -> tuple[int, int, Path]:
    issues_path = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "issues_json" / f"st_ready_issues_{repo.lower()}.json"
    resolver_path = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "resolver_cases_json" / f"st_ready_resolver_cases_{repo.lower()}.json"

    issues = load_json_array(issues_path, preferred_key="issues") if issues_path.exists() else []
    resolver_cases = load_json_array(resolver_path, preferred_key="resolver_cases") if resolver_path.exists() else []

    if not issues and not resolver_cases:
        raise FileNotFoundError(f"No ST-ready issue or resolver input found for repo {repo}")

    issue_index: dict[str, dict[str, Any]] = {}
    for issue in issues:
        if not include_all_issues and not issue.get("rescue_applied"):
            continue
        issue_number = issue.get("issue_number")
        if issue_number is None:
            continue
        issue_index[str(issue_number)] = issue

    resolver_index: dict[str, dict[str, Any]] = {}
    for case in resolver_cases:
        issue_number = case.get("issue_number")
        if issue_number is None:
            continue
        resolver_index[str(issue_number)] = case

    all_keys = sorted(set(issue_index.keys()) | set(resolver_index.keys()), key=lambda value: int(value) if value.isdigit() else value)
    cards: list[dict[str, Any]] = []
    for key in all_keys:
        cards.append(build_diagnostic_card(repo, issue_index.get(key), resolver_index.get(key)))

    out_root = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "diagnostic_cards_json"
    out_root.mkdir(parents=True, exist_ok=True)
    out_file = out_root / f"st_ready_diagnostic_cards_{repo.lower()}.json"
    out_file.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "repo": repo,
        "issues_input": str(issues_path) if issues_path.exists() else None,
        "resolver_input": str(resolver_path) if resolver_path.exists() else None,
        "output_file": str(out_file),
        "rescued_issues_considered": len(issue_index),
        "resolver_cases_considered": len(resolver_index),
        "exported_cards": len(cards),
        "include_all_issues": include_all_issues,
        "format": "json-array",
        "root_tag_path": "diagnostic_cards",
    }
    (out_root / f"summary_diagnostic_cards_{repo.lower()}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(issue_index) + len(resolver_index), len(cards), out_root


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export generic ST-ready diagnostic cards from rescued issues and resolver cases."
    )
    parser.add_argument("--repo", action="append", help="Repo name, e.g., STM32CubeH7. Can be repeated.")
    parser.add_argument(
        "--include-all-issues",
        action="store_true",
        help="Include all ST-ready issues instead of rescued issues only.",
    )
    args = parser.parse_args()

    cfg = load_config()
    repos = args.repo or cfg.get("repos", [])
    if not repos:
        raise ValueError("No repos provided and no repos found in config.")

    for repo in repos:
        try:
            total_inputs, exported, out_root = export_repo_json(
                repo=repo,
                include_all_issues=args.include_all_issues,
            )
        except FileNotFoundError as exc:
            print(f"[ST-READY:json:diagnostic_cards] {repo}: skipped ({exc})")
            continue
        print(
            f"[ST-READY:json:diagnostic_cards] {repo}: exported {exported} cards "
            f"from {total_inputs} source entries -> {out_root}"
        )

if __name__ == "__main__":
    main()