import argparse
import base64
import hashlib
import json
import mimetypes
import os
import random
import re
import runpy
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


DEFAULT_ENDPOINT = "https://api-ai-bridge.st.com/chatgpt/api/client-apps"
DEFAULT_SERVICE = "kb"
DEFAULT_TYPE_ADD = "kb-datasource-add"
DEFAULT_TYPE_NEW = "kb-datasource-new"
DEFAULT_TYPE_DELETE = "kb-datasource-delete"
DEFAULT_TYPE = DEFAULT_TYPE_ADD
LEGACY_TYPE_VARIANT_ADD = "kb-datasouce-add"
LEGACY_TYPE_VARIANT_NEW = "kb-datasouce-new"
LEGACY_TYPE_VARIANT_DELETE = "kb-datasouce-delete"
# Repository default client app for ST GitHub Analyzer persona.
DEFAULT_CLIENT_APP_NAME = "mdrf_st_github_analyzer"
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 60
RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}
DEFAULT_PAYLOAD_MODES = ["flat"]
DEFAULT_TIMESTAMP_MODES = ["s"]
BYTES_PER_MB = 1024 * 1024
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+\-']+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class ApiRejectedError(RuntimeError):
    def __init__(self, error_code: int | None, api_message: str, hint: str = "") -> None:
        self.error_code = error_code
        self.api_message = api_message
        self.hint = hint
        super().__init__(
            "Request reached API but was rejected. "
            f"Last API errorCode={error_code}, message={api_message}.{hint}"
        )


def repo_root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def default_search_dirs() -> list[Path]:
    root = repo_root_dir()
    return [
        root / "datasets" / "07_delivery" / "st_ready" / "issues_json",
        root / "datasets" / "07_delivery" / "st_ready" / "files_json",
        root / "datasets" / "07_delivery" / "st_ready" / "diagnostic_cards_json",
        root / "datasets" / "07_delivery" / "st_ready" / "resolver_cases_json",
        root / "data",
    ]


def generate_token(client_app_name: str, service_name: str, api_key: str, timestamp: int, nonce: int) -> str:
    data_string = f"{client_app_name}_{service_name}_{api_key}_{timestamp}_{nonce}"
    return hashlib.sha1(data_string.encode("utf-8")).hexdigest()


def _load_legacy_value(attr_name: str) -> Any:
    try:
        from Get_Persona_KBs import __dict__ as legacy_vars  # type: ignore

        return legacy_vars.get(attr_name)
    except Exception:
        # Fallback when launched from repo root where direct module import may fail.
        try:
            legacy_path = Path(__file__).resolve().parent / "Get_Persona_KBs.py"
            legacy_vars = runpy.run_path(str(legacy_path))
            return legacy_vars.get(attr_name)
        except Exception:
            return None
        


def looks_like_placeholder_api_key(value: str) -> bool:
    normalized = value.strip().lower()
    placeholders = {
        "ta_vraie_api_key",
        "ta_cle_reelle",
        "ma_cle_api",
        "ma_vraie_cle_api",
        "vraie_cle_api",
        "your_api_key",
        "replace_me",
        "api_key_here",
    }
    return (
        normalized in placeholders
        or "vraie_api_key" in normalized
        or "cle_reelle" in normalized
        or "vraie_cle_api" in normalized
    )


def resolve_api_key(cli_api_key: str | None) -> str:
    if cli_api_key and cli_api_key.strip():
        key = cli_api_key.strip()
        if looks_like_placeholder_api_key(key):
            raise ValueError(
                "Provided --api-key looks like a placeholder. "
                "Replace it with your real ST API key."
            )
        return key

    # Upload flows in this repository are bound to GitHub Analyzer identity.
    # Prefer analyzer credential first to avoid key/app mismatch when multiple
    # API key secrets are present in the environment.
    for env_name in (
        "ST_GITHUB_ANALYZER_API_KEY",
        "ST_CHATGPT_API_KEY",
        "ST_AI_BRIDGE_API_KEY",
        "ST_API_KEY",
        "PERSONA_API_KEY",
    ):
        value = os.getenv(env_name)
        if value and value.strip():
            key = value.strip()
            if looks_like_placeholder_api_key(key):
                raise ValueError(
                    f"Environment variable {env_name} contains a placeholder-like API key. "
                    "Replace it with your real ST API key."
                )
            return key

    legacy_key = _load_legacy_value("apiKey")
    if isinstance(legacy_key, str) and legacy_key.strip():
        return legacy_key.strip()

    raise ValueError(
        "Missing API key. Provide --api-key or set one of: "
        "ST_GITHUB_ANALYZER_API_KEY, PERSONA_API_KEY, ST_CHATGPT_API_KEY, ST_AI_BRIDGE_API_KEY, ST_API_KEY."
    )


def resolve_client_app_name(cli_name: str | None) -> str:
    if cli_name and cli_name.strip():
        return cli_name.strip()

    for env_name in ("ST_CHATGPT_CLIENT_APP", "ST_CLIENT_APP_NAME"):
        value = os.getenv(env_name)
        if value and value.strip():
            return value.strip()

    legacy_name = _load_legacy_value("clientAppName")
    if isinstance(legacy_name, str) and legacy_name.strip():
        return legacy_name.strip()

    return DEFAULT_CLIENT_APP_NAME


def resolve_proxies(use_legacy_proxy: bool) -> dict[str, str] | None:
    if not use_legacy_proxy:
        return None

    legacy_proxies = _load_legacy_value("proxies")
    if isinstance(legacy_proxies, dict):
        return {str(k): str(v) for k, v in legacy_proxies.items()}

    return None


def parse_processor_params(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None

    raw = raw.strip()
    if not raw:
        return None

    if raw.lower().startswith("base64:"):
        encoded = raw.split(":", 1)[1].strip()
        if not encoded:
            raise ValueError("--processor-params base64 payload is empty")
        try:
            decoded_bytes = base64.b64decode(encoded)
            raw = decoded_bytes.decode("utf-8")
        except Exception as exc:
            raise ValueError(f"Invalid base64 in --processor-params: {exc}") from exc
        raw = raw.strip()
        if not raw:
            return None

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        relaxed_value = parse_processor_params_relaxed(raw)
        if relaxed_value is not None:
            return relaxed_value
        raw_preview = raw if len(raw) <= 240 else f"{raw[:240]}..."
        raise ValueError(
            "Invalid JSON in --processor-params: "
            f"{exc}. Raw preview: {raw_preview}"
        ) from exc

    if not isinstance(value, dict):
        raise ValueError("--processor-params must be a JSON object")

    return value


def parse_processor_params_relaxed(raw: str) -> dict[str, Any] | None:
    """Best-effort parser for PowerShell-stripped JSON object arguments.

    Example accepted input:
    {label:{{repo}} issue #{{issue_number}},rootTagPath:issues,externalURL:https://...}
    """
    text = raw.strip()

    if (text.startswith('"') and text.endswith('"') and len(text) >= 2) or (
        text.startswith("'") and text.endswith("'") and len(text) >= 2
    ):
        text = text[1:-1].strip()

    if text.startswith("@"):
        text = text[1:].strip()

    if not (text.startswith("{") and text.endswith("}")):
        return None

    inner = text[1:-1].strip()
    if not inner:
        return {}

    parts: list[str] = []
    current: list[str] = []
    quote_char = ""
    escape = False

    for char in inner:
        if escape:
            current.append(char)
            escape = False
            continue

        if char == "\\":
            current.append(char)
            escape = True
            continue

        if quote_char:
            current.append(char)
            if char == quote_char:
                quote_char = ""
            continue

        if char in ('"', "'"):
            quote_char = char
            current.append(char)
            continue

        if char in (",", ";"):
            token = "".join(current).strip()
            if token:
                parts.append(token)
            current = []
            continue

        current.append(char)

    token = "".join(current).strip()
    if token:
        parts.append(token)

    if not parts:
        return {}

    parsed: dict[str, Any] = {}
    for part in parts:
        key_raw = ""
        value_raw = ""

        delimiter_index = -1
        quote_mode = ""
        escape_mode = False
        for idx, char in enumerate(part):
            if escape_mode:
                escape_mode = False
                continue
            if char == "\\":
                escape_mode = True
                continue
            if quote_mode:
                if char == quote_mode:
                    quote_mode = ""
                continue
            if char in ('"', "'"):
                quote_mode = char
                continue
            if char in (":", "="):
                delimiter_index = idx
                break

        if delimiter_index <= 0:
            return None

        key_raw = part[:delimiter_index]
        value_raw = part[delimiter_index + 1 :]
        key = key_raw.strip().strip("\"").strip("'")
        if not key:
            return None

        value_text = value_raw.strip()
        if (value_text.startswith('"') and value_text.endswith('"') and len(value_text) >= 2) or (
            value_text.startswith("'") and value_text.endswith("'") and len(value_text) >= 2
        ):
            value: Any = value_text[1:-1]
        else:
            lower_value = value_text.lower()
            if lower_value == "true":
                value = True
            elif lower_value == "false":
                value = False
            elif lower_value == "null":
                value = None
            else:
                value = value_text

        parsed[key] = value

    return parsed


def parse_csv_items(raw: str | None) -> list[str]:
    if raw is None:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def validate_remote_user_email(value: str) -> str:
    email = value.strip()
    if not email:
        raise ValueError("--remote-user is required")
    if email.count("@") != 1 or EMAIL_PATTERN.fullmatch(email) is None:
        raise ValueError(
            "--remote-user must be a valid email with a single '@' "
            "(example: first.last@st.com)."
        )
    return email


def normalize_request_types(raw: str | None, default_type: str) -> list[str]:
    parsed = parse_csv_items(raw)
    if parsed:
        dedup: list[str] = []
        seen: set[str] = set()
        for item in parsed:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)
        return dedup

    return [default_type]


def normalize_payload_modes(raw: str | None) -> list[str]:
    parsed = parse_csv_items(raw)
    if not parsed:
        return list(DEFAULT_PAYLOAD_MODES)

    modes: list[str] = []
    for mode in parsed:
        value = mode.lower()
        if value not in ("wrapped-json-part", "wrapped", "flat"):
            raise ValueError("--payload-modes supports only: wrapped-json-part, wrapped, flat")
        if value not in modes:
            modes.append(value)
    return modes


def normalize_timestamp_modes(raw: str | None) -> list[str]:
    parsed = parse_csv_items(raw)
    if not parsed:
        return list(DEFAULT_TIMESTAMP_MODES)

    modes: list[str] = []
    for mode in parsed:
        value = mode.lower()
        if value not in ("ms", "s"):
            raise ValueError("--timestamp-modes supports only: ms, s")
        if value not in modes:
            modes.append(value)
    return modes


def timestamp_from_mode(mode: str) -> int:
    if mode == "ms":
        return int(time.time() * 1000)
    if mode == "s":
        return int(time.time())
    raise ValueError(f"Unsupported timestamp mode: {mode}")


def api_error_info(response_json: Any) -> tuple[int | None, str]:
    if not isinstance(response_json, dict):
        return None, ""

    error_code = response_json.get("errorCode")
    if error_code in (None, 0, "0"):
        return None, ""

    message = str(response_json.get("message") or "").strip()

    try:
        numeric_code = int(error_code)
    except Exception:
        numeric_code = None

    return numeric_code, message


def is_timeout_like_success_payload(response_json: Any) -> bool:
    if not isinstance(response_json, dict):
        return False

    error_code = response_json.get("errorCode")
    if error_code not in (None, 0, "0"):
        return False

    message = str(response_json.get("message") or "").strip().lower()
    if not message:
        return False

    return message in {"request timeout", "timeout"} or "request timeout" in message


def is_non_retryable_api_rejection(error_code: int | None, message: str) -> bool:
    if error_code is None:
        return False

    normalized = (message or "").strip().lower()
    non_retryable_tokens = (
        "unexpected field",
        "remoteuser must be an email",
        "no documents found",
        "datasource must be a number",
        "could not find any entity of type \"kbdatasourceentity\"",
        "cannot upload files to deleted datasource",
        "datasource with name",
        "already exists",
        "invalid application name",
        "invalid auth token",
        "invalid timestamp",
        "invalid type",
        "invalid service type",
        "cannot upload existing file",
    )
    return any(token in normalized for token in non_retryable_tokens)


def is_existing_file_conflict(error_code: int | None, message: str) -> bool:
    if error_code != 3000:
        return False
    normalized = (message or "").strip().lower()
    return "cannot upload existing file" in normalized


def is_existing_datasource_name_conflict(error_code: int | None, message: str) -> bool:
    if error_code != 1000:
        return False
    normalized = (message or "").strip().lower()
    return "datasource with name" in normalized and "already exists" in normalized


def is_missing_datasource_entity_error(error_code: int | None, message: str) -> bool:
    if error_code != 1000:
        return False
    normalized = (message or "").strip().lower()
    return 'could not find any entity of type "kbdatasourceentity"' in normalized


def is_deleted_or_missing_datasource_error(error_code: int | None, message: str) -> bool:
    normalized = (message or "").strip().lower()
    if error_code == 3000 and "cannot upload files to deleted datasource" in normalized:
        return True
    return is_missing_datasource_entity_error(error_code, message)


def extract_existing_datasource_name(message: str) -> str | None:
    match = re.search(r'datasource with name\s+"([^"]+)"\s+already exists', message or "", flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def find_kb_entry_from_kb_list(kb_list_response: dict[str, Any], kb_id: int) -> dict[str, Any] | None:
    if not isinstance(kb_list_response, dict):
        return None

    kbs = kb_list_response.get("kbs")
    if not isinstance(kbs, list):
        return None

    for kb in kbs:
        if not isinstance(kb, dict):
            continue
        try:
            if int(kb.get("id")) == int(kb_id):
                return kb
        except Exception:
            continue

    if len(kbs) == 1 and isinstance(kbs[0], dict):
        return kbs[0]

    # Fallback: some API variants wrap payloads in nested objects.
    stack: list[Any] = [kb_list_response]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            nested_kbs = node.get("kbs")
            if isinstance(nested_kbs, list):
                for kb in nested_kbs:
                    if not isinstance(kb, dict):
                        continue
                    try:
                        if int(kb.get("id")) == int(kb_id):
                            return kb
                    except Exception:
                        continue
            for value in node.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, (dict, list)):
                    stack.append(item)

    return None


def list_datasource_entries_from_kb_entry(kb_entry: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(kb_entry, dict):
        return []

    data_sources = (
        kb_entry.get("dataSources")
        or kb_entry.get("datasources")
        or kb_entry.get("data_sources")
        or []
    )
    if not isinstance(data_sources, list):
        return []

    return [item for item in data_sources if isinstance(item, dict)]


def find_datasource_entry_from_kb_list(
    kb_list_response: dict[str, Any],
    kb_id: int,
    datasource_id: int | None,
    datasource_name: str | None,
) -> dict[str, Any] | None:
    kb_entry = find_kb_entry_from_kb_list(kb_list_response, kb_id)
    data_sources = list_datasource_entries_from_kb_entry(kb_entry)
    if not data_sources:
        return None

    if datasource_id is not None:
        for ds in data_sources:
            try:
                if int(ds.get("id")) == int(datasource_id):
                    return ds
            except Exception:
                continue

    if datasource_name and datasource_name.strip():
        wanted_exact = datasource_name.strip()
        wanted_lower = wanted_exact.lower()

        for ds in data_sources:
            ds_name = str(ds.get("name") or "").strip()
            if ds_name == wanted_exact:
                return ds

        for ds in data_sources:
            ds_name = str(ds.get("name") or "").strip()
            if ds_name.lower() == wanted_lower:
                return ds

    # Fallback: scan the full response in case dataSources are exposed in a different envelope.
    if datasource_name and datasource_name.strip():
        wanted_exact = datasource_name.strip()
        wanted_lower = wanted_exact.lower()
        stack: list[Any] = [kb_list_response]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                ds_name = str(node.get("name") or "").strip()
                ds_id = node.get("id")
                if ds_name and ds_id is not None:
                    try:
                        int(ds_id)
                        if ds_name == wanted_exact or ds_name.lower() == wanted_lower:
                            return node
                    except Exception:
                        pass
                for value in node.values():
                    if isinstance(value, (dict, list)):
                        stack.append(value)
            elif isinstance(node, list):
                for item in node:
                    if isinstance(item, (dict, list)):
                        stack.append(item)

    return None


def parse_json_object_like(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return dict(value)

    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                parsed = json.loads(text)
            except Exception:
                return None
            if isinstance(parsed, dict):
                return parsed

    return None


def extract_datasource_processor_config(
    datasource_entry: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any] | None]:
    if not isinstance(datasource_entry, dict):
        return None, None

    processor_keys = (
        "processor",
        "parser",
        "processorType",
        "processingType",
    )
    processor_params_keys = (
        "processorParams",
        "processor_params",
        "parserParams",
        "parser_params",
        "processorParameters",
        "parserParameters",
    )

    def pick_processor(container: dict[str, Any]) -> str | None:
        for key in processor_keys:
            raw = container.get(key)
            if not isinstance(raw, str):
                continue
            value = raw.strip()
            if not value:
                continue
            upper = value.upper()
            if upper in {"PDF", "JSON", "CSV", "STANDARD"}:
                return upper
            return value
        return None

    def pick_processor_params(container: dict[str, Any]) -> dict[str, Any] | None:
        for key in processor_params_keys:
            parsed = parse_json_object_like(container.get(key))
            if parsed is not None:
                return parsed
        return None

    processor = pick_processor(datasource_entry)
    processor_params = pick_processor_params(datasource_entry)

    for nested_key in ("config", "configuration", "settings", "options"):
        nested = datasource_entry.get(nested_key)
        if not isinstance(nested, dict):
            continue
        if processor is None:
            processor = pick_processor(nested)
        if processor_params is None:
            processor_params = pick_processor_params(nested)

    return processor, processor_params


def resolve_datasource_processor_config_from_kb_list(
    kb_list_response: dict[str, Any],
    kb_id: int,
    datasource_id: int | None,
    datasource_name: str | None,
) -> tuple[str | None, dict[str, Any] | None]:
    datasource_entry = find_datasource_entry_from_kb_list(
        kb_list_response=kb_list_response,
        kb_id=kb_id,
        datasource_id=datasource_id,
        datasource_name=datasource_name,
    )
    return extract_datasource_processor_config(datasource_entry)


def find_datasource_id_by_name_from_kb_list(
    kb_list_response: dict[str, Any],
    kb_id: int,
    datasource_name: str,
) -> int | None:
    datasource_entry = find_datasource_entry_from_kb_list(
        kb_list_response=kb_list_response,
        kb_id=kb_id,
        datasource_id=None,
        datasource_name=datasource_name,
    )
    if not isinstance(datasource_entry, dict):
        return None

    try:
        return int(datasource_entry.get("id"))
    except Exception:
        return None


def resolve_existing_datasource_id_by_name(
    endpoint: str,
    api_key: str,
    client_app_name: str,
    service_name: str,
    kb_id: int,
    datasource_name: str,
    timeout_seconds: int,
    verify_ssl: bool,
    proxies: dict[str, str] | None,
    verbose: bool,
) -> int | None:
    try:
        kb_list_response = run_auth_precheck(
            endpoint=endpoint,
            api_key=api_key,
            client_app_name=client_app_name,
            service_name=service_name,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
            proxies=proxies,
            verbose=verbose,
        )
    except Exception as exc:
        if verbose:
            print(
                "Failed to resolve datasource ID from kb-list after name conflict: "
                f"{exc}"
            )
        return None

    return find_datasource_id_by_name_from_kb_list(
        kb_list_response=kb_list_response,
        kb_id=kb_id,
        datasource_name=datasource_name,
    )


def resolve_datasource_id_from_local_config_by_name(datasource_name: str) -> int | None:
    match = re.match(
        r"^DB_STready_([A-Za-z0-9]+)_(Issues|Files|Diagnostic|Resolver)$",
        (datasource_name or "").strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    series = match.group(1).upper()
    kind = match.group(2).lower()
    kind_map = {
        "issues": "issues",
        "files": "files",
        "diagnostic": "diagnostic",
        "resolver": "resolver",
    }
    target_key = kind_map.get(kind)
    if not target_key:
        return None

    config_path = Path(__file__).resolve().parents[2] / "shared" / "config" / "config_all_series.json"
    if not config_path.exists():
        return None

    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

    ids_map = cfg.get("kb_datasource_ids") if isinstance(cfg, dict) else None
    if not isinstance(ids_map, dict):
        return None

    series_repo = f"STM32Cube{series}"
    entry = ids_map.get(series_repo)
    if not isinstance(entry, dict):
        return None

    value = entry.get(target_key)
    try:
        parsed = int(value)
        return parsed if parsed > 0 else None
    except Exception:
        return None


def resolve_datasource_id_from_delivery_snapshot_by_name(
    datasource_name: str,
    file_paths: list[Path],
) -> int | None:
    if not file_paths:
        return None

    match = re.match(
        r"^DB_STready_([A-Za-z0-9]+)_(Issues|Files|Diagnostic|Resolver)$",
        (datasource_name or "").strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    kind = match.group(2).lower()
    kind_map = {
        "issues": "issues",
        "files": "files",
        "diagnostic": "diagnostic",
        "resolver": "resolver",
    }
    target_key = kind_map.get(kind)
    if not target_key:
        return None

    first_path = file_paths[0].resolve()
    for parent in [first_path.parent, *first_path.parents]:
        if parent.name != "by_series":
            continue
        if len(first_path.parents) < 2:
            break

    # Walk up and locate by_series/<slug>/...
    current = first_path.parent
    by_series_dir: Path | None = None
    slug_dir: Path | None = None
    for _ in range(8):
        if current.name == "by_series":
            by_series_dir = current
            break
        if current.parent == current:
            break
        current = current.parent
    if by_series_dir is None:
        return None

    # slug is the direct child in the original path under by_series
    rel = first_path.relative_to(by_series_dir)
    if len(rel.parts) < 2:
        return None
    slug_dir = by_series_dir / rel.parts[0]
    snapshot_path = slug_dir / f"upload_datasource_ids_{rel.parts[0]}.json"
    if not snapshot_path.exists():
        return None

    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None

    value = payload.get(target_key)
    try:
        parsed = int(value)
        return parsed if parsed > 0 else None
    except Exception:
        return None


def extract_existing_filename(message: str) -> str | None:
    match = re.search(r'cannot upload existing file "([^"]+)"', message or "", flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


def is_split_part_filename(filename: str) -> bool:
    return re.search(r"__part\d+\.json$", filename or "", flags=re.IGNORECASE) is not None


def resolve_input_file_path(raw_item: str) -> Path:
    raw_path = Path(raw_item).expanduser()

    # 1) Provided path relative to current working directory.
    if raw_path.exists() and raw_path.is_file():
        return raw_path.resolve()

    # 2) Provided path relative to repository root.
    repo_relative = (repo_root_dir() / raw_path).resolve()
    if repo_relative.exists() and repo_relative.is_file():
        return repo_relative

    # 3) Bare filename: search common ST-ready output folders.
    if len(raw_path.parts) == 1:
        for folder in default_search_dirs():
            candidate = (folder / raw_path.name).resolve()
            if candidate.exists() and candidate.is_file():
                return candidate

    search_roots = [str(p) for p in default_search_dirs()]
    raise FileNotFoundError(
        "File not found: "
        f"{raw_item}.\n"
        f"Current directory: {Path.cwd()}\n"
        f"Also searched under: {search_roots}"
    )


def ensure_files_exist(paths: Iterable[str]) -> list[Path]:
    resolved: list[Path] = []
    for item in paths:
        path = resolve_input_file_path(item)
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        resolved.append(path)

    if not resolved:
        raise ValueError("At least one file is required")

    return resolved


def load_json_payload(path: Path) -> Any:
    try:
        content = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"Failed to read JSON file for upload: {path}: {exc}") from exc

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file for upload: {path.name}: {exc}") from exc


def detect_named_array_roots(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []

    keys: list[str] = []
    for key, value in payload.items():
        if isinstance(value, list):
            keys.append(str(key))
    return keys


def ensure_add_processor_compatibility(
    operation: str,
    datasource_id: int | None,
    processor: str | None,
    processor_params: dict[str, Any] | None,
    file_paths: list[Path],
) -> None:
    if operation != "add":
        return

    if not file_paths:
        return

    candidate_path: Path | None = None
    for path in file_paths:
        if path.suffix.lower() == ".json":
            candidate_path = path
            break

    if candidate_path is None:
        return

    try:
        payload = load_json_payload(candidate_path)
    except Exception:
        return

    root_keys = detect_named_array_roots(payload)
    if not root_keys:
        return

    root_keys_lower = {key.lower() for key in root_keys}
    processor_upper = (processor or "").strip().upper()
    keys_preview = ", ".join(root_keys) if root_keys else "<none>"

    if processor_upper == "STANDARD":
        raise ValueError(
            "Upload blocked before API call: target datasource appears configured with processor STANDARD "
            f"(id={datasource_id}), but JSON file {candidate_path.name} has object-root array key(s): [{keys_preview}]. "
            "This backend path expects array root for STANDARD processor. "
            "Use a datasource configured with processor JSON and processorParams rootTagPath='files', "
            "or delete/recreate this datasource with JSON configuration."
        )

    if processor_upper == "JSON":
        root_tag_path = None
        if isinstance(processor_params, dict):
            root_raw = processor_params.get("rootTagPath")
            if isinstance(root_raw, str) and root_raw.strip():
                root_tag_path = root_raw.strip()

        if not root_tag_path:
            raise ValueError(
                "Upload blocked before API call: processor JSON is selected for add upload, "
                f"but --processor-params rootTagPath is missing while JSON root keys are [{keys_preview}]. "
                "Set --processor-params with rootTagPath matching the payload key (for files use rootTagPath='files')."
            )

        if root_tag_path.lower() not in root_keys_lower:
            raise ValueError(
                "Upload blocked before API call: processor JSON rootTagPath does not match payload keys. "
                f"rootTagPath='{root_tag_path}', payload array key(s)=[{keys_preview}] in {candidate_path.name}."
            )
        return

    if processor_upper:
        return

    raise ValueError(
        "Upload blocked before API call: processor configuration is unknown for add upload "
        f"(datasource id={datasource_id}), and JSON file {candidate_path.name} has object-root key(s): [{keys_preview}]. "
        "This often ends with 'JSON root element is not an array' if datasource defaults to STANDARD. "
        "Use explicit --processor JSON with --processor-params rootTagPath, "
        "or upload to a datasource already configured as JSON."
    )


def flatten_json_root_array_file(source_path: Path, target_dir: Path, verbose: bool) -> tuple[Path, bool, bool]:
    payload = load_json_payload(source_path)

    if isinstance(payload, list):
        return source_path, False, len(payload) == 0

    if isinstance(payload, dict) and len(payload) == 1:
        key, value = next(iter(payload.items()))
        if isinstance(value, list):
            target_path = (target_dir / source_path.name).resolve()
            serialized = json.dumps(value, ensure_ascii=False)
            target_path.write_text(serialized, encoding="utf-8")
            if verbose:
                print(f"Auto-flattened JSON root for {source_path.name}: key '{key}' -> array")
            return target_path, True, len(value) == 0

    if isinstance(payload, dict) and len(payload) > 1:
        list_keys = [str(k) for k, v in payload.items() if isinstance(v, list)]
        preferred_keys = [
            "diagnostic_cards",
            "diagnosticCards",
            "resolver_cases",
            "issues",
            "files",
            "cards",
            "documents",
            "items",
            "data",
        ]

        selected_key: str | None = None
        for key in preferred_keys:
            if key in list_keys:
                selected_key = key
                break

        if selected_key is None and len(list_keys) == 1:
            selected_key = list_keys[0]

        if selected_key is not None:
            value = payload.get(selected_key)
            if isinstance(value, list):
                target_path = (target_dir / source_path.name).resolve()
                serialized = json.dumps(value, ensure_ascii=False)
                target_path.write_text(serialized, encoding="utf-8")
                if verbose:
                    print(
                        "Auto-flattened JSON root for "
                        f"{source_path.name}: key '{selected_key}' -> array "
                        f"(dict keys={list(payload.keys())})"
                    )
                return target_path, True, len(value) == 0

    if isinstance(payload, dict):
        keys = ", ".join(str(k) for k in payload.keys())
        raise ValueError(
            "Unsupported JSON root for processor JSON in file "
            f"{source_path.name}. Expected array root or object with one array field, got keys: [{keys}]"
        )

    raise ValueError(
        "Unsupported JSON root for processor JSON in file "
        f"{source_path.name}. Expected array or object."
    )


def extract_docs_array(payload: Any, root_tag_path: str | None) -> list[Any] | None:
    if root_tag_path:
        if not isinstance(payload, dict):
            return None

        value = payload.get(root_tag_path)
        if isinstance(value, list):
            return value

        for key, item in payload.items():
            if str(key).lower() == root_tag_path.lower() and isinstance(item, list):
                return item

        return None

    if isinstance(payload, list):
        return payload

    return None


def normalize_json_for_upload(
    source_path: Path,
    target_dir: Path,
    root_tag_path: str | None,
    verbose: bool,
) -> tuple[Path, bool, bool]:
    payload = load_json_payload(source_path)

    if root_tag_path:
        docs_array = extract_docs_array(payload, root_tag_path)
        if docs_array is not None:
            if isinstance(payload, dict) and root_tag_path in payload:
                return source_path, False, len(docs_array) == 0

            target_path = (target_dir / source_path.name).resolve()
            wrapped = {root_tag_path: docs_array}
            target_path.write_text(json.dumps(wrapped, ensure_ascii=False), encoding="utf-8")
            if verbose:
                print(
                    "Normalized JSON root for "
                    f"{source_path.name}: wrapped array under key '{root_tag_path}'"
                )
            return target_path, True, len(docs_array) == 0

        if isinstance(payload, list):
            target_path = (target_dir / source_path.name).resolve()
            wrapped = {root_tag_path: payload}
            target_path.write_text(json.dumps(wrapped, ensure_ascii=False), encoding="utf-8")
            if verbose:
                print(
                    "Normalized JSON root for "
                    f"{source_path.name}: array -> key '{root_tag_path}'"
                )
            return target_path, True, len(payload) == 0

        if isinstance(payload, dict):
            keys = ", ".join(str(k) for k in payload.keys())
            raise ValueError(
                "Unsupported JSON root for processor JSON in file "
                f"{source_path.name}. Expected key '{root_tag_path}' with array, got keys: [{keys}]"
            )

        raise ValueError(
            "Unsupported JSON root for processor JSON in file "
            f"{source_path.name}. Expected object with key '{root_tag_path}'."
        )

    return flatten_json_root_array_file(source_path, target_dir, verbose)


def prepare_file_paths_for_upload(
    file_paths: list[Path],
    processor: str | None,
    processor_params: dict[str, Any] | None,
    json_root_mode: str,
    empty_json_policy: str,
    json_split_size: int,
    json_split_min_mb: float,
    verbose: bool,
) -> tuple[list[Path], Path | None, list[str]]:
    if processor != "JSON" or json_root_mode != "auto" or not file_paths:
        return file_paths, None, []

    temp_dir = Path(tempfile.mkdtemp(prefix="st_kb_json_upload_"))
    prepared_paths: list[Path] = []
    skipped_empty_files: list[str] = []
    transformed_count = 0
    split_parts_count = 0
    root_tag_path: str | None = None

    if isinstance(processor_params, dict):
        root_value = processor_params.get("rootTagPath")
        if isinstance(root_value, str) and root_value.strip():
            root_tag_path = root_value.strip()

    for source_path in file_paths:
        prepared_path, transformed, is_empty_array = normalize_json_for_upload(
            source_path=source_path,
            target_dir=temp_dir,
            root_tag_path=root_tag_path,
            verbose=verbose,
        )

        if is_empty_array:
            if empty_json_policy == "skip":
                skipped_empty_files.append(source_path.name)
                if verbose:
                    print(f"Skipping empty JSON payload file: {source_path.name}")
                continue
            if empty_json_policy == "fail":
                raise ValueError(
                    "Empty JSON payload detected in file "
                    f"{source_path.name}. Use --empty-json-policy skip or upload."
                )

        if json_split_size > 0:
            payload_for_split = load_json_payload(prepared_path)
            docs_for_split = extract_docs_array(payload_for_split, root_tag_path)
            if docs_for_split is not None and len(docs_for_split) > json_split_size:
                file_size_bytes = prepared_path.stat().st_size
                split_min_bytes = int(json_split_min_mb * BYTES_PER_MB)

                if split_min_bytes > 0 and file_size_bytes < split_min_bytes:
                    if verbose:
                        size_mb = file_size_bytes / BYTES_PER_MB
                        print(
                            "Not splitting JSON payload file "
                            f"{source_path.name}: {size_mb:.2f} MB is below "
                            f"--json-split-min-mb {json_split_min_mb:g}"
                        )
                    prepared_paths.append(prepared_path)
                    if transformed:
                        transformed_count += 1
                    continue

                part_paths: list[Path] = []
                part_index = 1
                for start_idx in range(0, len(docs_for_split), json_split_size):
                    part_docs = docs_for_split[start_idx : start_idx + json_split_size]
                    if root_tag_path:
                        part_payload: Any = {root_tag_path: part_docs}
                    else:
                        part_payload = part_docs
                    part_path = (temp_dir / f"{source_path.stem}__part{part_index:03d}.json").resolve()
                    part_path.write_text(
                        json.dumps(part_payload, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    part_paths.append(part_path)
                    part_index += 1

                if verbose:
                    size_mb = file_size_bytes / BYTES_PER_MB
                    print(
                        "Split JSON payload file "
                        f"{source_path.name} into {len(part_paths)} parts "
                        f"(max {json_split_size} docs/part, source {size_mb:.2f} MB)"
                    )

                prepared_paths.extend(part_paths)
                split_parts_count += len(part_paths)
                if transformed:
                    transformed_count += 1
                continue

        prepared_paths.append(prepared_path)
        if transformed:
            transformed_count += 1

    if transformed_count == 0 and split_parts_count == 0:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return prepared_paths, None, skipped_empty_files

    if verbose:
        root_note = f" (rootTagPath={root_tag_path})" if root_tag_path else ""
        print(
            "Prepared JSON files for upload with normalized JSON root"
            f"{root_note}: {transformed_count}/{len(file_paths)} transformed"
        )
        if skipped_empty_files:
            print(f"Skipped empty JSON payload files: {len(skipped_empty_files)}")
        if split_parts_count:
            print(f"Created split JSON upload parts: {split_parts_count}")

    return prepared_paths, temp_dir, skipped_empty_files


def build_datasource_payload(
    operation: str,
    datasource_id: int | None,
    datasource_name: str | None,
    datasource_classification: str,
    datasource_tags: list[str],
    processor: str | None,
    processor_params: dict[str, Any] | None,
) -> Any:
    if operation == "add":
        if datasource_id is None:
            raise ValueError("--datasource-id is required when --operation add")
        datasource: Any = {"id": datasource_id}
    elif operation == "delete":
        if datasource_id is None:
            raise ValueError("--datasource-id is required when --operation delete")
        datasource = datasource_id
    elif operation == "new":
        if not datasource_name or not datasource_name.strip():
            raise ValueError("--datasource-name is required when --operation new")

        datasource = {
            "name": datasource_name.strip(),
            "classification": datasource_classification,
        }

        if datasource_tags:
            datasource["tags"] = datasource_tags
    else:
        raise ValueError(f"Unsupported operation: {operation}")

    if operation in ("add", "new"):
        if processor:
            datasource["processor"] = processor

        if processor_params:
            datasource["processorParams"] = processor_params

    return datasource


def build_payload(
    client_app_name: str,
    remote_user: str,
    kb_id: int,
    datasource_payload: Any,
    service_name: str,
    request_type: str,
    timestamp_value: int,
) -> dict[str, Any]:
    return {
        "version": 1,
        "clientAppName": client_app_name,
        "timestamp": timestamp_value,
        "remoteUser": remote_user,
        "service": service_name,
        "type": request_type,
        "kb": kb_id,
        "datasource": datasource_payload,
    }


def open_files_for_multipart(file_paths: list[Path]) -> tuple[list[tuple[str, tuple[str, Any, str]]], list[Any]]:
    files_parts: list[tuple[str, tuple[str, Any, str]]] = []
    handles: list[Any] = []

    for path in file_paths:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        handle = path.open("rb")
        handles.append(handle)
        files_parts.append(("files", (path.name, handle, mime_type)))

    return files_parts, handles


def post_datasource_request(
    endpoint: str,
    api_key: str,
    auth_service_name: str,
    client_app_name: str,
    payload: dict[str, Any],
    payload_mode: str,
    request_part_name: str | None,
    file_paths: list[Path],
    timeout_seconds: int,
    verify_ssl: bool,
    proxies: dict[str, str] | None,
) -> requests.Response:
    timestamp = payload["timestamp"]
    nonce = random.randint(0, 999999)
    token = generate_token(client_app_name, auth_service_name, api_key, timestamp, nonce)

    headers = {
        "stchatgpt-auth-token": token,
        "stchatgpt-auth-nonce": str(nonce),
        "Accept": "application/json",
    }

    # Requests without files (e.g. datasource delete) are sent as JSON body to
    # preserve numeric field types such as datasource IDs.
    if not file_paths:
        return requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=timeout_seconds,
            verify=verify_ssl,
            proxies=proxies,
        )

    files_parts, handles = open_files_for_multipart(file_paths)

    if payload_mode == "wrapped-json-part":
        if not request_part_name:
            raise ValueError("request_part_name is required for wrapped-json-part payload mode")
        json_payload = json.dumps(payload, ensure_ascii=True)
        # Attach request metadata as a JSON part in multipart body.
        files_parts.append((request_part_name, ("request.json", json_payload, "application/json")))
        form_data: dict[str, str] = {}
    elif payload_mode == "wrapped":
        if not request_part_name:
            raise ValueError("request_part_name is required for wrapped payload mode")
        form_data: dict[str, str] = {request_part_name: json.dumps(payload, ensure_ascii=True)}
    elif payload_mode == "flat":
        form_data = {
            "version": str(payload.get("version")),
            "clientAppName": str(payload.get("clientAppName") or ""),
            "timestamp": str(payload.get("timestamp")),
            "remoteUser": str(payload.get("remoteUser") or ""),
            "service": str(payload.get("service") or ""),
            "type": str(payload.get("type") or ""),
            "kb": str(payload.get("kb")),
            "datasource": json.dumps(payload.get("datasource") or {}, ensure_ascii=True),
        }
    else:
        raise ValueError(f"Unsupported payload_mode: {payload_mode}")

    try:
        return requests.post(
            endpoint,
            data=form_data,
            files=files_parts,
            headers=headers,
            timeout=timeout_seconds,
            verify=verify_ssl,
            proxies=proxies,
        )
    finally:
        for handle in handles:
            try:
                handle.close()
            except Exception:
                pass


def run_auth_precheck(
    endpoint: str,
    api_key: str,
    client_app_name: str,
    service_name: str,
    timeout_seconds: int,
    verify_ssl: bool,
    proxies: dict[str, str] | None,
    verbose: bool,
) -> dict[str, Any]:
    timestamp_value = int(time.time())
    nonce = random.randint(0, 999999)
    token = generate_token(client_app_name, service_name, api_key, timestamp_value, nonce)

    headers = {
        "stchatgpt-auth-token": token,
        "stchatgpt-auth-nonce": str(nonce),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "version": 1,
        "clientAppName": client_app_name,
        "timestamp": timestamp_value,
        "service": service_name,
        "type": "kb-list",
    }

    if verbose:
        print(
            "Running auth precheck with kb-list "
            f"clientAppName='{client_app_name}' service='{service_name}'"
        )

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=timeout_seconds,
            verify=verify_ssl,
            proxies=proxies,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Auth precheck request failed: {exc}") from exc

    response_text = (response.text or "")[:2000]
    if response.status_code != 200:
        raise RuntimeError(
            "Auth precheck failed. "
            f"HTTP status={response.status_code}, body={response_text}"
        )

    try:
        response_json = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Auth precheck returned HTTP 200 but invalid JSON response: "
            f"{response_text}"
        ) from exc

    error_code, error_message = api_error_info(response_json)
    if error_code is None:
        if verbose:
            print("Auth precheck succeeded.")
        return response_json

    hint = ""
    normalized_message = error_message.lower()
    if error_code == 2000 and "invalid auth token" in normalized_message:
        hint = " Hint: verify --api-key secret and --client-app-name persona binding."
    elif error_code == 2000 and "invalid application name" in normalized_message:
        hint = " Hint: provide a valid --client-app-name or omit the flag for auto-resolution."
    elif error_code == 2000 and "invalid timestamp" in normalized_message:
        hint = " Hint: verify local system time and auth timestamp mode."

    raise ApiRejectedError(error_code, f"Auth precheck rejected: {error_message}", hint)


def run_datasource_request(
    endpoint: str,
    api_key: str,
    client_app_name: str,
    service_name: str,
    remote_user: str,
    kb_id: int,
    datasource_payload: Any,
    file_paths: list[Path],
    request_types: list[str],
    request_part_names: list[str],
    payload_modes: list[str],
    timestamp_modes: list[str],
    max_retries: int,
    timeout_seconds: int,
    verify_ssl: bool,
    proxies: dict[str, str] | None,
    verbose: bool,
) -> dict[str, Any]:
    last_exception: Exception | None = None
    last_status: int | None = None
    last_text = ""
    last_api_error_code: int | None = None
    last_api_error_message = ""
    saw_non_retryable_api_rejection = False

    for attempt in range(1, max_retries + 1):
        for timestamp_mode in timestamp_modes:
            timestamp_value = timestamp_from_mode(timestamp_mode)
            for request_type in request_types:
                payload = build_payload(
                    client_app_name=client_app_name,
                    remote_user=remote_user,
                    kb_id=kb_id,
                    datasource_payload=datasource_payload,
                    service_name=service_name,
                    request_type=request_type,
                    timestamp_value=timestamp_value,
                )

                for payload_mode in payload_modes:
                    if payload_mode in ("wrapped", "wrapped-json-part"):
                        iter_part_names: list[str | None] = list(request_part_names)
                    else:
                        iter_part_names = [None]

                    for part_name in iter_part_names:
                        if verbose:
                            part_info = f"{payload_mode}/{part_name}" if part_name else payload_mode
                            print(
                                f"[Attempt {attempt}/{max_retries}] POST {endpoint} "
                                f"type='{request_type}' mode='{part_info}' ts='{timestamp_mode}' files={len(file_paths)}"
                            )

                        try:
                            response = post_datasource_request(
                                endpoint=endpoint,
                                api_key=api_key,
                                auth_service_name=service_name,
                                client_app_name=client_app_name,
                                payload=payload,
                                payload_mode=payload_mode,
                                request_part_name=part_name,
                                file_paths=file_paths,
                                timeout_seconds=timeout_seconds,
                                verify_ssl=verify_ssl,
                                proxies=proxies,
                            )
                        except requests.RequestException as exc:
                            last_exception = exc
                            if verbose:
                                print(f"Network error: {exc}")
                            continue

                        last_status = response.status_code
                        last_text = (response.text or "")[:2000]

                        if response.status_code == 200:
                            try:
                                data = response.json()
                            except ValueError as exc:
                                raise RuntimeError(f"HTTP 200 but invalid JSON response: {last_text}") from exc

                            api_error_code, api_error_message = api_error_info(data)
                            if api_error_code is None:
                                if is_timeout_like_success_payload(data):
                                    if verbose:
                                        print(
                                            "API timeout-like response despite HTTP 200; "
                                            "retrying with alternate payload/retry loop. "
                                            f"message={str(data.get('message') or '')}"
                                        )
                                    continue
                                return data

                            last_api_error_code = api_error_code
                            last_api_error_message = api_error_message
                            if is_non_retryable_api_rejection(api_error_code, api_error_message):
                                saw_non_retryable_api_rejection = True
                            if verbose:
                                print(
                                    "API error response: "
                                    f"errorCode={api_error_code}, message={api_error_message}"
                                )
                            continue

                        if verbose:
                            print(f"HTTP {response.status_code}: {last_text}")

                        # Try next request format on client-side input/validation errors.
                        if response.status_code in (400, 401, 403, 404, 405, 415, 422):
                            continue

                        # For transient backend errors, break and retry with backoff.
                        if response.status_code in RETRYABLE_HTTP_CODES:
                            break

        if saw_non_retryable_api_rejection:
            if verbose and attempt < max_retries:
                print("Non-retryable API rejection detected; skipping further retries.")
            break

        if attempt < max_retries:
            sleep_seconds = 2 ** attempt
            if verbose:
                print(f"Retrying in {sleep_seconds} second(s)...")
            time.sleep(sleep_seconds)

    if last_exception is not None and last_status is None:
        raise RuntimeError(f"Request failed with network errors: {last_exception}") from last_exception

    if last_api_error_code is not None:
        hint = ""
        normalized_message = last_api_error_message.lower()
        if last_api_error_code == 2000 and "invalid application name" in normalized_message:
            candidate_name = ""
            legacy_name = _load_legacy_value("clientAppName")
            if isinstance(legacy_name, str) and legacy_name.strip():
                candidate_name = legacy_name.strip()

            if candidate_name:
                hint = f" Hint: use --client-app-name '{candidate_name}' or omit the flag to use auto-resolution."
            else:
                hint = " Hint: provide a valid --client-app-name for your ST persona."
        elif last_api_error_code == 2000 and "invalid timestamp" in normalized_message:
            hint = " Hint: use --timestamp-modes s (seconds)."
        elif last_api_error_code == 2000 and "invalid auth token" in normalized_message:
            hint = " Hint: verify --api-key is the real secret and that --client-app-name matches your persona app."
        elif last_api_error_code == 1000 and "remoteuser must be an email" in normalized_message:
            hint = " Hint: set --remote-user to a real email like first.last@st.com (single '@')."
        elif last_api_error_code == 1000 and "datasource must be a number" in normalized_message:
            hint = " Hint: for delete requests, --datasource-id must be a valid integer ID."
        elif (
            last_api_error_code == 1000
            and "could not find any entity of type \"kbdatasourceentity\"" in normalized_message
        ):
            hint = " Hint: this datasource ID does not exist (already deleted or invalid)."
        elif last_api_error_code == 3000 and "cannot upload files to deleted datasource" in normalized_message:
            hint = " Hint: this datasource ID is deleted; upload with --operation new to create a fresh datasource."
        elif "no documents found" in normalized_message:
            hint = " Hint: JSON file contains no records; use --empty-json-policy skip to ignore empty files."
        elif last_api_error_code == 1000 and "invalid type" in normalized_message:
            hint = (
                " Hint: remove --request-types add_datasource_file and use the default add type "
                f"'{DEFAULT_TYPE_ADD}', or pass --request-types {DEFAULT_TYPE_ADD}."
            )
        elif last_api_error_code == 1000 and "unexpected field" in normalized_message:
            hint = " Hint: use --payload-modes flat for this endpoint."
        elif last_api_error_code == 3000 and "cannot upload existing file" in normalized_message:
            hint = " Hint: existing file in datasource; in add mode, use default skip behavior or --fail-on-existing-files to enforce strict mode."

        raise ApiRejectedError(last_api_error_code, last_api_error_message, hint)

    raise RuntimeError("Datasource request failed. " f"Last HTTP status={last_status}, body={last_text}")


def run_add_request_skip_existing_files(
    endpoint: str,
    api_key: str,
    client_app_name: str,
    service_name: str,
    remote_user: str,
    kb_id: int,
    datasource_payload: dict[str, Any],
    file_paths: list[Path],
    request_types: list[str],
    request_part_names: list[str],
    payload_modes: list[str],
    timestamp_modes: list[str],
    max_retries: int,
    timeout_seconds: int,
    verify_ssl: bool,
    proxies: dict[str, str] | None,
    fail_on_existing_files: bool,
    verbose: bool,
) -> dict[str, Any]:
    uploaded_files: list[str] = []
    skipped_existing_files: list[str] = []
    last_response: dict[str, Any] | None = None

    for path in file_paths:
        try:
            response = run_datasource_request(
                endpoint=endpoint,
                api_key=api_key,
                client_app_name=client_app_name,
                service_name=service_name,
                remote_user=remote_user,
                kb_id=kb_id,
                datasource_payload=datasource_payload,
                file_paths=[path],
                request_types=request_types,
                request_part_names=request_part_names,
                payload_modes=payload_modes,
                timestamp_modes=timestamp_modes,
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
                verify_ssl=verify_ssl,
                proxies=proxies,
                verbose=verbose,
            )
            if isinstance(response, dict):
                last_response = response
            uploaded_files.append(path.name)
        except ApiRejectedError as exc:
            if is_existing_file_conflict(exc.error_code, exc.api_message):
                existing_name = extract_existing_filename(exc.api_message) or path.name
                if fail_on_existing_files and not is_split_part_filename(existing_name):
                    raise RuntimeError(
                        "Upload blocked: existing file conflict detected for "
                        f"'{existing_name}' while strict mode is enabled. "
                        "In replace mode this usually means datasource clear did not complete as expected."
                    )
                if fail_on_existing_files and verbose and is_split_part_filename(existing_name):
                    print(
                        "Strict mode: tolerated existing conflict for split upload part "
                        f"'{existing_name}' (idempotent retry scenario)."
                    )
                skipped_existing_files.append(existing_name)
                if verbose:
                    print(f"Skipping existing file already in datasource: {existing_name}")
                continue
            raise

    if last_response is None:
        last_response = {
            "service": service_name,
            "type": request_types[0] if request_types else DEFAULT_TYPE_ADD,
            "datasource": datasource_payload.get("id"),
        }

    last_response["uploaded_files"] = uploaded_files
    if skipped_existing_files:
        last_response["skipped_existing_files"] = skipped_existing_files

    if not uploaded_files and skipped_existing_files:
        last_response["message"] = (
            "No new files uploaded. All selected files already exist in datasource. "
            "To reload corrected content, create a new datasource (operation=new) "
            "or delete old files first, then upload again."
        )

    return last_response


def run_new_request_with_followup_add(
    endpoint: str,
    api_key: str,
    client_app_name: str,
    service_name: str,
    remote_user: str,
    kb_id: int,
    datasource_payload: dict[str, Any],
    file_paths: list[Path],
    request_types: list[str],
    request_part_names: list[str],
    payload_modes: list[str],
    timestamp_modes: list[str],
    max_retries: int,
    timeout_seconds: int,
    verify_ssl: bool,
    proxies: dict[str, str] | None,
    existing_datasource_policy: str,
    fail_on_existing_files: bool,
    verbose: bool,
) -> dict[str, Any]:
    if not file_paths:
        raise ValueError("At least one file is required for --operation new")

    datasource_name = str(datasource_payload.get("name") or "").strip()
    requested_processor = datasource_payload.get("processor") if isinstance(datasource_payload, dict) else None
    requested_processor_params = (
        datasource_payload.get("processorParams") if isinstance(datasource_payload, dict) else None
    )
    created_datasource_name_used = datasource_name

    # Create the datasource with the first file, then add remaining files one by one.
    # This avoids oversized multipart requests for large split sets.
    first_path = file_paths[0]
    try:
        create_response = run_datasource_request(
            endpoint=endpoint,
            api_key=api_key,
            client_app_name=client_app_name,
            service_name=service_name,
            remote_user=remote_user,
            kb_id=kb_id,
            datasource_payload=datasource_payload,
            file_paths=[first_path],
            request_types=request_types,
            request_part_names=request_part_names,
            payload_modes=payload_modes,
            timestamp_modes=timestamp_modes,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
            proxies=proxies,
            verbose=verbose,
        )
    except ApiRejectedError as exc:
        if not is_existing_datasource_name_conflict(exc.error_code, exc.api_message):
            raise

        conflict_name = extract_existing_datasource_name(exc.api_message) or datasource_name
        if not conflict_name:
            raise

        existing_datasource_id = resolve_existing_datasource_id_by_name(
            endpoint=endpoint,
            api_key=api_key,
            client_app_name=client_app_name,
            service_name=service_name,
            kb_id=kb_id,
            datasource_name=conflict_name,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
            proxies=proxies,
            verbose=verbose,
        )

        if existing_datasource_id is None:
            resolve_attempts = 5
            resolve_delay_seconds = 3
            for attempt in range(2, resolve_attempts + 1):
                if verbose:
                    print(
                        "Datasource name conflict detected but ID unresolved; retrying lookup "
                        f"({attempt}/{resolve_attempts}) after {resolve_delay_seconds}s..."
                    )
                time.sleep(resolve_delay_seconds)
                existing_datasource_id = resolve_existing_datasource_id_by_name(
                    endpoint=endpoint,
                    api_key=api_key,
                    client_app_name=client_app_name,
                    service_name=service_name,
                    kb_id=kb_id,
                    datasource_name=conflict_name,
                    timeout_seconds=timeout_seconds,
                    verify_ssl=verify_ssl,
                    proxies=proxies,
                    verbose=verbose,
                )
                if existing_datasource_id is not None:
                    break

        if existing_datasource_id is None:
            local_fallback_id = resolve_datasource_id_from_local_config_by_name(conflict_name)
            if local_fallback_id is not None:
                existing_datasource_id = local_fallback_id
                if verbose:
                    print(
                        "Datasource ID resolved from shared/config/config_all_series.json "
                        f"for '{conflict_name}': {existing_datasource_id}"
                    )

        if existing_datasource_id is None:
            snapshot_fallback_id = resolve_datasource_id_from_delivery_snapshot_by_name(
                conflict_name,
                file_paths,
            )
            if snapshot_fallback_id is not None:
                existing_datasource_id = snapshot_fallback_id
                if verbose:
                    print(
                        "Datasource ID resolved from upload_datasource_ids snapshot "
                        f"for '{conflict_name}': {existing_datasource_id}"
                    )

        if existing_datasource_id is None:
            raise RuntimeError(
                "Datasource name conflict detected, but existing datasource ID "
                f"could not be resolved for '{conflict_name}' after retries. "
                "Aborting to avoid duplicate datasource creation. "
                "Retry later or resolve the duplicate manually in KB Management."
            )
        if existing_datasource_id is not None:
            if verbose:
                print(
                    "Datasource already exists by name; switching to add mode on existing ID "
                    f"{existing_datasource_id}."
                )

            if existing_datasource_policy == "replace":
                if verbose:
                    print(
                        "Existing datasource policy=replace: using in-place upload on resolved datasource ID "
                        f"{existing_datasource_id} to avoid delete/recreate conflicts."
                    )

                add_payload: dict[str, Any] = {"id": existing_datasource_id}
                if requested_processor:
                    add_payload["processor"] = requested_processor
                if requested_processor_params:
                    add_payload["processorParams"] = requested_processor_params

                try:
                    add_replace_response = run_add_request_skip_existing_files(
                        endpoint=endpoint,
                        api_key=api_key,
                        client_app_name=client_app_name,
                        service_name=service_name,
                        remote_user=remote_user,
                        kb_id=kb_id,
                        datasource_payload=add_payload,
                        file_paths=file_paths,
                        request_types=[DEFAULT_TYPE_ADD],
                        request_part_names=request_part_names,
                        payload_modes=payload_modes,
                        timestamp_modes=timestamp_modes,
                        max_retries=max_retries,
                        timeout_seconds=timeout_seconds,
                        verify_ssl=verify_ssl,
                        proxies=proxies,
                        fail_on_existing_files=fail_on_existing_files,
                        verbose=verbose,
                    )
                except ApiRejectedError as add_exc:
                    if not is_deleted_or_missing_datasource_error(add_exc.error_code, add_exc.api_message):
                        raise

                    # Re-resolve ID if the one we had is stale/deleted.
                    fallback_candidates: list[int] = []

                    resolved_from_api = resolve_existing_datasource_id_by_name(
                        endpoint=endpoint,
                        api_key=api_key,
                        client_app_name=client_app_name,
                        service_name=service_name,
                        kb_id=kb_id,
                        datasource_name=conflict_name,
                        timeout_seconds=timeout_seconds,
                        verify_ssl=verify_ssl,
                        proxies=proxies,
                        verbose=verbose,
                    )
                    if resolved_from_api is not None:
                        fallback_candidates.append(resolved_from_api)

                    resolved_from_snapshot = resolve_datasource_id_from_delivery_snapshot_by_name(conflict_name, file_paths)
                    if resolved_from_snapshot is not None:
                        fallback_candidates.append(resolved_from_snapshot)

                    resolved_from_config = resolve_datasource_id_from_local_config_by_name(conflict_name)
                    if resolved_from_config is not None:
                        fallback_candidates.append(resolved_from_config)

                    ordered_candidates: list[int] = []
                    seen_ids: set[int] = set()
                    for candidate in fallback_candidates:
                        if candidate in seen_ids or candidate == existing_datasource_id:
                            continue
                        seen_ids.add(candidate)
                        ordered_candidates.append(candidate)

                    if existing_datasource_id not in seen_ids:
                        ordered_candidates.append(existing_datasource_id)

                    if not ordered_candidates:
                        raise RuntimeError(
                            f"Conflict for '{conflict_name}' and stale datasource ID {existing_datasource_id}; "
                            "could not resolve a live datasource ID for fallback add."
                        ) from add_exc

                    retry_success = False
                    last_retry_exc: ApiRejectedError | None = None
                    for candidate_id in ordered_candidates:
                        add_payload_retry: dict[str, Any] = {"id": candidate_id}
                        if requested_processor:
                            add_payload_retry["processor"] = requested_processor
                        if requested_processor_params:
                            add_payload_retry["processorParams"] = requested_processor_params

                        try:
                            add_replace_response = run_add_request_skip_existing_files(
                                endpoint=endpoint,
                                api_key=api_key,
                                client_app_name=client_app_name,
                                service_name=service_name,
                                remote_user=remote_user,
                                kb_id=kb_id,
                                datasource_payload=add_payload_retry,
                                file_paths=file_paths,
                                request_types=[DEFAULT_TYPE_ADD],
                                request_part_names=request_part_names,
                                payload_modes=payload_modes,
                                timestamp_modes=timestamp_modes,
                                max_retries=max_retries,
                                timeout_seconds=timeout_seconds,
                                verify_ssl=verify_ssl,
                                proxies=proxies,
                                fail_on_existing_files=fail_on_existing_files,
                                verbose=verbose,
                            )
                            existing_datasource_id = candidate_id
                            retry_success = True
                            break
                        except ApiRejectedError as retry_exc:
                            if is_deleted_or_missing_datasource_error(retry_exc.error_code, retry_exc.api_message):
                                last_retry_exc = retry_exc
                                continue
                            raise

                    if not retry_success:
                        tried = ", ".join(str(cid) for cid in ordered_candidates)
                        raise RuntimeError(
                            f"Conflict for '{conflict_name}' and stale datasource ID {existing_datasource_id}; "
                            f"fallback add failed for candidate datasource IDs: [{tried}]"
                        ) from last_retry_exc

                final_replace = dict(add_replace_response)
                final_replace["datasource"] = existing_datasource_id
                final_replace.setdefault(
                    "message",
                    (
                        f'Datasource "{conflict_name}" already existed; '
                        "replace policy executed with in-place upload on existing datasource."
                    ),
                )
                return final_replace

            elif verbose:
                print(
                    "Existing datasource policy=add: appending files to existing datasource content "
                    f"(datasource id {existing_datasource_id})."
                )

            add_datasource_payload: dict[str, Any] = {"id": existing_datasource_id}
            if requested_processor:
                add_datasource_payload["processor"] = requested_processor
            if requested_processor_params:
                add_datasource_payload["processorParams"] = requested_processor_params

            add_response = run_add_request_skip_existing_files(
                endpoint=endpoint,
                api_key=api_key,
                client_app_name=client_app_name,
                service_name=service_name,
                remote_user=remote_user,
                kb_id=kb_id,
                datasource_payload=add_datasource_payload,
                file_paths=file_paths,
                request_types=[DEFAULT_TYPE_ADD],
                request_part_names=request_part_names,
                payload_modes=payload_modes,
                timestamp_modes=timestamp_modes,
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
                verify_ssl=verify_ssl,
                proxies=proxies,
                fail_on_existing_files=fail_on_existing_files,
                verbose=verbose,
            )

            final_existing = dict(add_response)
            final_existing["datasource"] = existing_datasource_id
            if existing_datasource_policy == "replace":
                final_existing.setdefault(
                    "message",
                    (
                        f'Datasource "{conflict_name}" already existed; existing content was deleted '
                        "and fresh files were uploaded (replace mode)."
                    ),
                )
            else:
                final_existing.setdefault(
                    "message",
                    (
                        f'Datasource "{conflict_name}" already existed; files were appended '
                        "to the existing datasource (add mode)."
                    ),
                )
            return final_existing

    datasource_id_raw = create_response.get("datasource") if isinstance(create_response, dict) else None
    try:
        datasource_id = int(datasource_id_raw)
    except Exception as exc:
        raise RuntimeError(
            "Datasource created but response does not include a numeric datasource ID: "
            f"{datasource_id_raw!r}"
        ) from exc

    final_response = dict(create_response)
    uploaded_files: list[str] = [first_path.name]
    skipped_existing_files: list[str] = []

    remaining_paths = file_paths[1:]
    if remaining_paths:
        add_datasource_payload: dict[str, Any] = {"id": datasource_id}
        if requested_processor:
            add_datasource_payload["processor"] = requested_processor
        if requested_processor_params:
            add_datasource_payload["processorParams"] = requested_processor_params

        add_response = run_add_request_skip_existing_files(
            endpoint=endpoint,
            api_key=api_key,
            client_app_name=client_app_name,
            service_name=service_name,
            remote_user=remote_user,
            kb_id=kb_id,
            datasource_payload=add_datasource_payload,
            file_paths=remaining_paths,
            request_types=[DEFAULT_TYPE_ADD],
            request_part_names=request_part_names,
            payload_modes=payload_modes,
            timestamp_modes=timestamp_modes,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
            proxies=proxies,
            fail_on_existing_files=fail_on_existing_files,
            verbose=verbose,
        )

        uploaded_files.extend(add_response.get("uploaded_files", []))
        skipped_existing_files.extend(add_response.get("skipped_existing_files", []))

    final_response["datasource"] = datasource_id
    final_response["uploaded_files"] = uploaded_files
    if created_datasource_name_used:
        final_response["datasource_name_used"] = created_datasource_name_used
    if skipped_existing_files:
        final_response["skipped_existing_files"] = skipped_existing_files

    return final_response


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a datasource, add files, or delete datasource files in an ST KB datasource"
    )

    parser.add_argument("--kb", type=int, required=True, help="Knowledge base ID")
    parser.add_argument(
        "--operation",
        choices=["add", "new", "delete"],
        default="add",
        help=(
            "Datasource operation: "
            "add (existing datasource), new (create datasource), or delete (delete all files in datasource)"
        ),
    )
    parser.add_argument(
        "--datasource-id",
        type=int,
        help="Datasource ID to update when --operation add/delete",
    )
    parser.add_argument("--datasource-name", help="Datasource name when --operation new")
    parser.add_argument(
        "--datasource-classification",
        default="PUBLIC",
        help="Datasource classification when --operation new (default: PUBLIC)",
    )
    parser.add_argument(
        "--datasource-tags",
        default="",
        help="Optional comma-separated datasource tags when --operation new",
    )
    parser.add_argument("--remote-user", required=True, help="Remote user email (ex: john.smith@st.com)")
    parser.add_argument("--files", nargs="+", help="One or more files to upload (required for --operation add)")

    parser.add_argument("--processor", choices=["PDF", "JSON", "CSV", "STANDARD"], help="Optional datasource processor")
    parser.add_argument("--processor-params", help="Optional processor params as JSON object")
    parser.add_argument(
        "--inherit-datasource-processor",
        dest="inherit_datasource_processor",
        action="store_true",
        default=True,
        help=(
            "In add mode, inherit missing processor/processorParams from existing datasource via kb-list "
            "(default: enabled)"
        ),
    )
    parser.add_argument(
        "--no-inherit-datasource-processor",
        dest="inherit_datasource_processor",
        action="store_false",
        help="Disable datasource processor inheritance in add mode",
    )
    parser.add_argument(
        "--json-root-mode",
        choices=["auto", "raw"],
        default="auto",
        help="For processor JSON: auto-flatten object roots to arrays when possible (default: auto)",
    )
    parser.add_argument(
        "--empty-json-policy",
        choices=["skip", "upload", "fail"],
        default="skip",
        help=(
            "For processor JSON with auto root mode: behavior for empty arrays. "
            "skip=ignore empty files (default), upload=send anyway, fail=stop with error"
        ),
    )
    parser.add_argument(
        "--json-split-size",
        type=int,
        default=0,
        help=(
            "For processor JSON with auto root mode: split each array payload into parts "
            "with at most N docs per upload file (0 disables split)"
        ),
    )
    parser.add_argument(
        "--json-split-min-mb",
        type=float,
        default=0.0,
        help=(
            "For processor JSON with --json-split-size: split only if source JSON file size "
            "is >= this threshold in MB (0 disables size threshold)"
        ),
    )

    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="API endpoint URL")
    parser.add_argument("--service", default=DEFAULT_SERVICE, help="Service value in payload (default: kb)")
    parser.add_argument(
        "--request-type",
        help="Primary request type value in payload (defaults by operation)",
    )
    parser.add_argument(
        "--request-types",
        help="Optional comma-separated request type candidates to try in order",
    )
    parser.add_argument(
        "--payload-modes",
        default="flat",
        help="Comma-separated payload modes to try: wrapped-json-part, wrapped, flat (recommended: flat)",
    )
    parser.add_argument(
        "--timestamp-modes",
        default="s",
        help="Comma-separated timestamp modes to try: ms,s (recommended: s)",
    )
    parser.add_argument("--client-app-name", help="Client app name (defaults to env or legacy script value)")
    parser.add_argument("--api-key", help="API key (defaults to env or legacy script value)")
    parser.add_argument(
        "--auth-check-only",
        action="store_true",
        help="Run authentication precheck only (kb-list) and exit",
    )
    parser.add_argument(
        "--skip-auth-precheck",
        action="store_true",
        help="Skip auth precheck before upload",
    )
    parser.add_argument(
        "--request-part-names",
        default="request,body,payload",
        help="Comma-separated request part names to try for JSON metadata",
    )
    parser.add_argument(
        "--fail-on-existing-files",
        action="store_true",
        help="In add mode, fail if files already exist in datasource (default: skip existing files)",
    )
    parser.add_argument(
        "--existing-datasource-policy",
        choices=["replace", "add"],
        default="replace",
        help=(
            "When --operation new and datasource name already exists: "
            "replace (delete then add, default) or add (append)."
        ),
    )
    parser.add_argument(
        "--delete-not-found-policy",
        choices=["fail", "ignore"],
        default="fail",
        help=(
            "Behavior for --operation delete when datasource does not exist: "
            "fail (default) or ignore"
        ),
    )

    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="Maximum retry count")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="HTTP timeout in seconds")

    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Enable SSL certificate verification (disabled by default for compatibility)",
    )
    parser.add_argument(
        "--use-legacy-proxy",
        action="store_true",
        help="Reuse proxy settings from Get_Persona_KBs.py",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose logs")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    remote_user = validate_remote_user_email(args.remote_user)
    api_key = resolve_api_key(args.api_key)
    client_app_name = resolve_client_app_name(args.client_app_name)
    processor_params = parse_processor_params(args.processor_params)
    effective_processor = args.processor
    effective_processor_params = processor_params
    file_paths = ensure_files_exist(args.files) if args.files else []
    temp_dir_for_upload: Path | None = None
    kb_list_response: dict[str, Any] | None = None

    if args.operation in ("add", "delete") and args.datasource_id is None and not args.auth_check_only:
        raise ValueError(f"--datasource-id is required when --operation {args.operation}")
    if args.operation == "add" and not file_paths and not args.auth_check_only:
        raise ValueError("--files is required when --operation add")
    if args.operation == "delete" and file_paths:
        raise ValueError("--files is not supported when --operation delete")
    if args.operation == "new" and (not args.datasource_name or not args.datasource_name.strip()) and not args.auth_check_only:
        raise ValueError("--datasource-name is required when --operation new")

    if args.operation == "add":
        default_request_type = DEFAULT_TYPE_ADD
    elif args.operation == "new":
        default_request_type = DEFAULT_TYPE_NEW
    else:
        default_request_type = DEFAULT_TYPE_DELETE

    request_type = args.request_type.strip() if isinstance(args.request_type, str) and args.request_type.strip() else default_request_type
    request_types = normalize_request_types(args.request_types, request_type)
    payload_modes = normalize_payload_modes(args.payload_modes)
    timestamp_modes = normalize_timestamp_modes(args.timestamp_modes)
    datasource_tags = parse_csv_items(args.datasource_tags)

    if args.json_split_size < 0:
        raise ValueError("--json-split-size must be >= 0")
    if args.json_split_min_mb < 0:
        raise ValueError("--json-split-min-mb must be >= 0")

    needs_datasource_processor_inheritance = (
        not args.auth_check_only
        and args.operation == "add"
        and args.datasource_id is not None
        and args.inherit_datasource_processor
        and (not effective_processor or effective_processor_params is None)
    )

    if args.auth_check_only:
        datasource_payload: dict[str, Any] = {}
    else:
        datasource_payload = build_datasource_payload(
            operation=args.operation,
            datasource_id=args.datasource_id,
            datasource_name=args.datasource_name,
            datasource_classification=args.datasource_classification,
            datasource_tags=datasource_tags,
            processor=effective_processor,
            processor_params=effective_processor_params,
        )

    request_part_names = [part.strip() for part in args.request_part_names.split(",") if part.strip()]
    if not request_part_names:
        raise ValueError("--request-part-names cannot be empty")

    proxies = resolve_proxies(args.use_legacy_proxy)

    if not args.skip_auth_precheck or needs_datasource_processor_inheritance:
        if args.skip_auth_precheck and needs_datasource_processor_inheritance and args.verbose:
            print(
                "skip-auth-precheck is set, but datasource processor inheritance requires kb-list; "
                "running kb-list once for metadata lookup."
            )

        kb_list_response = run_auth_precheck(
            endpoint=args.endpoint,
            api_key=api_key,
            client_app_name=client_app_name,
            service_name=args.service,
            timeout_seconds=max(5, args.timeout),
            verify_ssl=args.verify_ssl,
            proxies=proxies,
            verbose=args.verbose,
        )

    if args.auth_check_only:
        print("Auth precheck completed successfully.")
        return

    if needs_datasource_processor_inheritance:
        inherited_processor, inherited_params = resolve_datasource_processor_config_from_kb_list(
            kb_list_response=kb_list_response or {},
            kb_id=args.kb,
            datasource_id=args.datasource_id,
            datasource_name=None,
        )

        inherited_any = False
        if not effective_processor and inherited_processor:
            effective_processor = inherited_processor
            inherited_any = True

        if effective_processor_params is None and inherited_params is not None:
            effective_processor_params = inherited_params
            inherited_any = True

        if inherited_any and isinstance(datasource_payload, dict):
            if effective_processor:
                datasource_payload["processor"] = effective_processor
            if isinstance(effective_processor_params, dict):
                datasource_payload["processorParams"] = effective_processor_params

            if args.verbose:
                root_tag = None
                if isinstance(effective_processor_params, dict):
                    root_raw = effective_processor_params.get("rootTagPath")
                    if isinstance(root_raw, str) and root_raw.strip():
                        root_tag = root_raw.strip()
                print(
                    "Inherited datasource processor config from kb-list: "
                    f"processor={effective_processor}, rootTagPath={root_tag or '<none>'}"
                )
        elif args.verbose:
            print(
                "No datasource processor config inherited from kb-list; "
                "continuing with explicit CLI values only."
            )

    if args.operation == "delete":
        try:
            response_json = run_datasource_request(
                endpoint=args.endpoint,
                api_key=api_key,
                client_app_name=client_app_name,
                service_name=args.service,
                remote_user=remote_user,
                kb_id=args.kb,
                datasource_payload=datasource_payload,
                file_paths=[],
                request_types=request_types,
                request_part_names=request_part_names,
                payload_modes=payload_modes,
                timestamp_modes=timestamp_modes,
                max_retries=max(1, args.max_retries),
                timeout_seconds=max(5, args.timeout),
                verify_ssl=args.verify_ssl,
                proxies=proxies,
                verbose=args.verbose,
            )
        except ApiRejectedError as exc:
            normalized_message = (exc.api_message or "").lower()
            not_found = (
                exc.error_code == 1000
                and "could not find any entity of type \"kbdatasourceentity\"" in normalized_message
            )
            if not_found and args.delete_not_found_policy == "ignore":
                response_json = {
                    "service": args.service,
                    "type": request_types[0] if request_types else default_request_type,
                    "datasource": args.datasource_id,
                    "files": [],
                    "message": (
                        "Datasource not found; treated as already deleted "
                        f"(id={args.datasource_id})."
                    ),
                }
                if args.verbose:
                    print(response_json["message"])
            else:
                raise
        print("Datasource response:")
        print(json.dumps(response_json, ensure_ascii=True, indent=2))
        return

    ensure_add_processor_compatibility(
        operation=args.operation,
        datasource_id=args.datasource_id,
        processor=effective_processor,
        processor_params=effective_processor_params,
        file_paths=file_paths,
    )

    prepared_file_paths, temp_dir_for_upload, skipped_empty_files = prepare_file_paths_for_upload(
        file_paths=file_paths,
        processor=effective_processor,
        processor_params=effective_processor_params,
        json_root_mode=args.json_root_mode,
        empty_json_policy=args.empty_json_policy,
        json_split_size=args.json_split_size,
        json_split_min_mb=args.json_split_min_mb,
        verbose=args.verbose,
    )

    if skipped_empty_files:
        print(
            "Skipped empty JSON files before upload: "
            f"{len(skipped_empty_files)}"
        )

    if not prepared_file_paths:
        if args.operation == "add":
            response_json = {
                "service": args.service,
                "type": request_types[0] if request_types else default_request_type,
                "datasource": datasource_payload.get("id"),
                "uploaded_files": [],
                "skipped_empty_files": skipped_empty_files,
                "message": "No upload performed: all selected JSON files are empty.",
            }
            print("Datasource response:")
            print(json.dumps(response_json, ensure_ascii=True, indent=2))
            return
        raise ValueError(
            "All selected files are empty JSON arrays; nothing to upload for --operation new. "
            "Use --empty-json-policy upload to force upload."
        )

    try:
        if args.operation == "add" and not args.fail_on_existing_files:
            response_json = run_add_request_skip_existing_files(
                endpoint=args.endpoint,
                api_key=api_key,
                client_app_name=client_app_name,
                service_name=args.service,
                remote_user=remote_user,
                kb_id=args.kb,
                datasource_payload=datasource_payload,
                file_paths=prepared_file_paths,
                request_types=request_types,
                request_part_names=request_part_names,
                payload_modes=payload_modes,
                timestamp_modes=timestamp_modes,
                max_retries=max(1, args.max_retries),
                timeout_seconds=max(5, args.timeout),
                verify_ssl=args.verify_ssl,
                proxies=proxies,
                fail_on_existing_files=args.fail_on_existing_files,
                verbose=args.verbose,
            )
        elif args.operation == "new":
            response_json = run_new_request_with_followup_add(
                endpoint=args.endpoint,
                api_key=api_key,
                client_app_name=client_app_name,
                service_name=args.service,
                remote_user=remote_user,
                kb_id=args.kb,
                datasource_payload=datasource_payload,
                file_paths=prepared_file_paths,
                request_types=request_types,
                request_part_names=request_part_names,
                payload_modes=payload_modes,
                timestamp_modes=timestamp_modes,
                max_retries=max(1, args.max_retries),
                timeout_seconds=max(5, args.timeout),
                verify_ssl=args.verify_ssl,
                proxies=proxies,
                existing_datasource_policy=args.existing_datasource_policy,
                fail_on_existing_files=args.fail_on_existing_files,
                verbose=args.verbose,
            )
        else:
            response_json = run_datasource_request(
                endpoint=args.endpoint,
                api_key=api_key,
                client_app_name=client_app_name,
                service_name=args.service,
                remote_user=remote_user,
                kb_id=args.kb,
                datasource_payload=datasource_payload,
                file_paths=prepared_file_paths,
                request_types=request_types,
                request_part_names=request_part_names,
                payload_modes=payload_modes,
                timestamp_modes=timestamp_modes,
                max_retries=max(1, args.max_retries),
                timeout_seconds=max(5, args.timeout),
                verify_ssl=args.verify_ssl,
                proxies=proxies,
                verbose=args.verbose,
            )
    finally:
        if temp_dir_for_upload is not None:
            shutil.rmtree(temp_dir_for_upload, ignore_errors=True)

    print("Datasource response:")
    print(json.dumps(response_json, ensure_ascii=True, indent=2))

    datasource = response_json.get("datasource") if isinstance(response_json, dict) else None
    if datasource is not None:
        print(f"\nDatasource ID returned: {datasource}")


if __name__ == "__main__":
    main()
