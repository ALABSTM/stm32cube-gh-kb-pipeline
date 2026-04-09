import re
from typing import Any
from urllib.parse import quote

from pipeline.chunking.chunk_service import mcu_series_from_repo
from pipeline.enrichment.stm32cube_preprocessing_heuristics import detect_layer, detect_severity


def classify_issue_kind(text: str, labels: list[str]) -> str:
    labels_lower = [lbl.lower() for lbl in labels]

    if "bug" in labels_lower or "internal bug tracker" in labels_lower:
        return "bug_report"

    txt_lower = text.lower()
    if "how to" in txt_lower or "how do i" in txt_lower or "question" in labels_lower:
        return "usage_question"

    if "configuration" in txt_lower or "configure" in txt_lower or "clock configuration" in txt_lower:
        return "configuration_help"

    return "other"


def has_invalid_label(labels: list[str]) -> bool:
    labels_lower = [lbl.lower() for lbl in labels]
    return any(lbl in ("invalid", "duplicate", "wontfix") for lbl in labels_lower)


BOARD_REGEXES = [
    r"NUCLEO-[A-Z0-9]+",
    r"STM32H7[0-9A-Z]+",
    r"STM32F4[0-9A-Z]+",
    r"STM32F7[0-9A-Z]+",
]


def detect_board(text: str) -> str | None:
    txt_upper = text.upper()
    for pattern in BOARD_REGEXES:
        match = re.search(pattern, txt_upper)
        if match:
            return match.group(0)
    return None


COMPONENT_KEYWORDS = {
    "ETH": ["ethernet", " lan ", " eth "],
    "USB": ["usb", "usb device", "usb_device"],
    "ADC": ["adc"],
    "DMA": [" dma "],
    "UART": ["uart", "usart"],
    "CAN": ["fdcan", " bxcan", " hal_can_", " can1", " can2", "can bus", "canfd"],
    "FREERTOS": ["freertos"],
}


def detect_component(text: str) -> str | None:
    txt_lower = f" {text.lower()} "
    for component, keywords in COMPONENT_KEYWORDS.items():
        for kw in keywords:
            if kw in txt_lower:
                return component
    return None


def build_file_github_url(repo: str | None, path: str | None, owner: str = "STMicroelectronics") -> str | None:
    if not repo or not path:
        return None
    path_norm = path.replace("\\", "/").lstrip("/")
    path_escaped = quote(path_norm, safe="/")
    return f"https://github.com/{owner}/{repo}/blob/master/{path_escaped}"


class PreprocessingConfig:
    def __init__(self, version: str = "v2.0") -> None:
        self.version = version
        self.enable_filtering = True
        self.enable_issue_kind = True
        self.enable_board_detection = True
        self.enable_component_detection = True


class PreprocessingModelIssuesV2:
    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        self.config = config or PreprocessingConfig()

    def process_clean_issue(self, issue: dict[str, Any]) -> dict[str, Any]:
        repo = issue.get("repo")
        issue_number = issue.get("issue_number")
        labels: list[str] = issue.get("labels") or []
        labels_lower = [lbl.lower() for lbl in labels]

        clean_text: str = issue.get("clean_text") or ""

        is_confirmed_bug = any(lbl in ("bug", "internal bug tracker") for lbl in labels_lower)

        is_valid = True
        if self.config.enable_filtering:
            if len(clean_text) < 100:
                is_valid = False
            if has_invalid_label(labels):
                is_valid = False

        doc: dict[str, Any] = {
            "id": f"{(repo or '').lower()}-issue-{issue_number}",
            "source_kind": "issue",
            "repo": repo,
            "mcu_package": repo,
            "mcu_series": mcu_series_from_repo(repo),
            "type": "issue",
            "path": None,
            "github_url": issue.get("github_url"),
            "board": None,
            "category": None,
            "component": None,
            "example_name": None,
            "issue_number": issue_number,
            "issue_title": issue.get("title") or "",
            "state": issue.get("state"),
            "labels": labels,
            "is_confirmed_bug": is_confirmed_bug,
            "created_at": issue.get("created_at"),
            "closed_at": issue.get("closed_at"),
            "ingest_version": self.config.version,
            "clean_text": clean_text,
            "image_urls": issue.get("image_urls") or [],
            "images_count": issue.get("images_count") or 0,
            "is_valid": is_valid,
        }

        doc["layer"] = detect_layer(clean_text)
        doc["severity"] = detect_severity(clean_text, labels)

        if self.config.enable_issue_kind:
            doc["issue_kind"] = classify_issue_kind(clean_text, labels)

        if self.config.enable_board_detection:
            board = detect_board(clean_text)
            if board:
                doc["board"] = board

        if self.config.enable_component_detection:
            component = detect_component(clean_text)
            if component:
                doc["component"] = component

        return doc


class PreprocessingModelFilesV2:
    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        self.config = config or PreprocessingConfig()

    def process_clean_file(self, file_obj: dict[str, Any]) -> dict[str, Any]:
        repo = file_obj.get("repo")
        path = file_obj.get("path") or ""
        clean_text: str = file_obj.get("clean_text") or ""
        file_type: str = file_obj.get("file_type") or "other"

        doc_id = f"{(repo or '').lower()}-file-{abs(hash(path))}"
        is_valid = len(clean_text) >= 100

        doc: dict[str, Any] = {
            "id": doc_id,
            "source_kind": "file",
            "repo": repo,
            "mcu_package": repo,
            "mcu_series": mcu_series_from_repo(repo),
            "type": "file",
            "path": path,
            "file_type": file_type,
            "github_url": file_obj.get("github_url") or build_file_github_url(repo=repo, path=path),
            "board": None,
            "category": None,
            "component": None,
            "example_name": None,
            "ingest_version": self.config.version,
            "clean_text": clean_text,
            "is_valid": is_valid,
        }

        text_for_detection = path + "\n" + clean_text

        board = detect_board(text_for_detection)
        if board:
            doc["board"] = board

        component = detect_component(text_for_detection)
        if component:
            doc["component"] = component

        parts = path.replace("\\", "/").split("/")
        if "Examples" in parts:
            idx = parts.index("Examples")
            if idx + 1 < len(parts):
                doc["example_name"] = parts[idx + 1]

        return doc
