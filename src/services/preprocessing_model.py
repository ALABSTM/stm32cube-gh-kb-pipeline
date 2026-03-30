import re
from typing import Any

from src.services.chunk_service import mcu_series_from_repo
from src.services.stm32cube_preprocessing_heuristics import (
    detect_layer,
    detect_severity,
)



def classify_issue_kind(text: str, labels: list[str]) -> str:
    """
    Classe simple pour V2 :
    - bug_report
    - usage_question
    - configuration_help
    - other
    """
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
    """
    Retourne True si l'issue est marquée comme invalide / duplicate / wontfix
    via les labels GitHub.
    """
    labels_lower = [lbl.lower() for lbl in labels]
    return any(lbl in ("invalid", "duplicate", "wontfix") for lbl in labels_lower)


BOARD_REGEXES = [
    r"NUCLEO-[A-Z0-9]+",
    r"STM32H7[0-9A-Z]+",
    r"STM32F4[0-9A-Z]+",
    r"STM32F7[0-9A-Z]+",
    
]


def detect_board(text: str) -> str | None:
    """
    Détection simple de la carte à partir du texte.
    """
    txt_upper = text.upper()
    for pattern in BOARD_REGEXES:
        m = re.search(pattern, txt_upper)
        if m:
            return m.group(0)
    return None


COMPONENT_KEYWORDS = {
    "ETH": ["ethernet", " lan ", " eth "],
    "USB": ["usb", "usb device", "usb_device"],
    "ADC": ["adc"],
    "DMA": [" dma "],
    "UART": ["uart", "usart"],
    "CAN": [
        "fdcan",
        " bxcan",
        " hal_can_",
        " can1",
        " can2",
        "can bus",
        "canfd",
    ],
    "FREERTOS": ["freertos"],
}


def detect_component(text: str) -> str | None:
    txt_lower = f" {text.lower()} "
    for component, keywords in COMPONENT_KEYWORDS.items():
        for kw in keywords:
            if kw in txt_lower:
                return component
    return None

class PreprocessingConfig:
    def __init__(self, version: str = "v2.0") -> None:
        self.version = version
        self.enable_filtering = True
        self.enable_issue_kind = True
        self.enable_board_detection = True
        self.enable_component_detection = True
   


class PreprocessingModelIssuesV2:
    """
    Modèle de prétraitement V2 pour les issues STM32Cube.

    Entrée : issue nettoyée (clean_issues_*).
    Sortie : document enrichi (docs_issues_v2).
    """

    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        self.config = config or PreprocessingConfig()

    def process_clean_issue(self, issue: dict[str, Any]) -> dict[str, Any]:
        repo = issue.get("repo")
        issue_number = issue.get("issue_number")
        labels: list[str] = issue.get("labels") or []
        labels_lower = [lbl.lower() for lbl in labels]

        clean_text: str = issue.get("clean_text") or ""
        created_at = issue.get("created_at")
        closed_at = issue.get("closed_at")

        # bug confirmé (déjà en V1)
        is_confirmed_bug = any(lbl in ("bug", "internal bug tracker") for lbl in labels_lower)

        # Filtrage V2 : is_valid 
        is_valid = True
        if self.config.enable_filtering:
            # 1) texte trop court
            if len(clean_text) < 100:
                is_valid = False

            # 2) labels invalid/duplicate/wontfix
            if has_invalid_label(labels):
                is_valid = False

        # Métadonnées de base (comme V1 + is_valid)
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
            "created_at": created_at,
            "closed_at": closed_at,
            "ingest_version": self.config.version,
            "clean_text": clean_text,
            "image_urls": issue.get("image_urls") or [],
            "images_count": issue.get("images_count") or 0,
            "is_valid": is_valid,
        }


        # V2.1 : couche logicielle
        doc["layer"] = detect_layer(clean_text)

        # V2.1 : sévérité heuristique
        doc["severity"] = detect_severity(clean_text, labels)

        # V2 : classification issue_kind par règles
        if self.config.enable_issue_kind:
            doc["issue_kind"] = classify_issue_kind(clean_text, labels)

        # V2 : détection board
        if self.config.enable_board_detection:
            board = detect_board(clean_text)
            if board:
                doc["board"] = board

        # V2 : détection component
        if self.config.enable_component_detection:
            component = detect_component(clean_text)
            if component:
                doc["component"] = component

        return doc


class PreprocessingModelFilesV2:
    """
    Modèle de prétraitement V2 pour les fichiers STM32Cube (README, Release Notes, Projects).
    Entrée : fichier nettoyé (clean_files_*).
    Sortie : document enrichi (docs_files_v2).
    """

    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        self.config = config or PreprocessingConfig()

    def process_clean_file(self, file_obj: dict[str, Any]) -> dict[str, Any]:
        repo = file_obj.get("repo")
        path = file_obj.get("path") or ""
        clean_text: str = file_obj.get("clean_text") or ""
        file_type: str = file_obj.get("file_type") or "other"

        # id simple basé sur le path
        doc_id = f"{(repo or '').lower()}-file-{abs(hash(path))}"

        # validité minimale : texte suffisant
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
            "github_url": None,  
            "board": None,
            "category": None,
            "component": None,
            "example_name": None,
            "ingest_version": self.config.version,
            "clean_text": clean_text,
            "is_valid": is_valid,
        }

        # Détection board / component sur path + contenu
        text_for_detection = path + "\n" + clean_text

        board = detect_board(text_for_detection)
        if board:
            doc["board"] = board

        component = detect_component(text_for_detection)
        if component:
            doc["component"] = component

        # Extraction du nom d'exemple si dans Projects/.../Examples/<ExampleName>/...
        parts = path.replace("\\", "/").split("/")
        if "Examples" in parts:
            idx = parts.index("Examples")
            if idx + 1 < len(parts):
                doc["example_name"] = parts[idx + 1]

        return doc