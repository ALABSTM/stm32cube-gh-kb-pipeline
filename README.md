1. Contexte général du PFE
PFE chez STMicroelectronics (Tunis), sur un projet :
“PFE 2026 – AI-powered Chatbot for GitHub (STM32Cube)”.
Idée de départ (PFE Book) : développer un chatbot RAG pour le support client à partir des dépôts GitHub STM32Cube.
État réel chez ST :
ST a déjà un moteur RAG interne (plateforme STChatGPT / Nova / ALFRED, etc.).
Ils ne veulent pas que le PFE développe un deuxième RAG concurrent.
Nouvelle orientation validée avec les encadrants :
Le PFE se concentre sur un pipeline de prétraitement intelligent (“AI-powered preprocessing pipeline”) qui :
ingère, nettoie et structure les données STM32Cube GitHub (issues + fichiers),
produit une base de connaissances “RAG‑ready” (docs_, chunks_),
fournit plusieurs versions de prétraitement (V1 simple, V2 heuristique, V3 plus tard avec IA),
et est évalué via des scripts de tests (stats, similarité, TF‑IDF search).
En résumé, ton PFE = pipeline de data & preprocessing pour RAG, pas un chatbot complet.

2. Périmètre des données
2.1. Issues GitHub
Repos ciblés (exemples) :
STM32CubeH7
STM32CubeH5
(possibilité d’extension à d’autres familles plus tard).
Données issues :
titre, description, labels, état (open/closed), dates,
commentaires, liens GitHub,
images (URLs, compte).
2.2. Fichiers GitHub
Fichiers textuels dans les repos STM32Cube :
README.md à la racine,
Projects/**/README*.(md|txt),
Release_Notes*.(md|txt|html|htm),
README éventuels sous Documentation/.
Contenu : documentation globale, exemples de projets, notes de version, etc.
3. Architecture actuelle du projet (PC ST)
Arborescence simplifiée :

text
PFE_Chatbot_STM32Cube/
  .github/           # config Copilot Agent (VS Code) pour aide à la doc/évaluation
    agents/
      STM32CubePreprocessing.agent.md
    skills/
      analyze_stats/
        SKILL.md

  data/
    raw_issues_stm32cubeh7.json
    clean_issues_stm32cubeh7.json
    docs_issues_stm32cubeh7_v2.json
    docs_issues_stm32cubeh7_v2_sim.json
    chunks_issues_stm32cubeh7_v2.json
    raw_files_stm32cubeh7.json
    clean_files_stm32cubeh7.json
    docs_files_stm32cubeh7_v2.json
    chunks_files_stm32cubeh7_v2.json
    ... (idem pour H5, etc.)

  GitHub_repos/
    STM32CubeH7/   # repo cloné
    STM32CubeH5/   # ...

  src/
    config/
      ... (config json, liste des repos, version de preprocessing, etc.)
    scripts/
      fetch_issues.py
      clean_issues.py
      issues_to_docs_v2.py
      compute_issue_similarity_v2.py
      docs_to_chunks_issues_v2.py
      fetch_files.py
      clean_files.py
      files_to_docs_v2.py
      docs_to_chunks_files_v2.py
      test_stats_issues_v2.py
      test_stats_files_v2.py
      test_consistency_issues_v2_vs_sim.py
      test_tfidf_search_issues_v2.py
      test_tfidf_search_files_v2.py
    services/
      github_service.py          # ingestion issues via API GitHub
      cleaning_service.py        # nettoyage des issues
      chunk_service.py           # utilitaires de chunking et mcu_series_from_repo
      file_collect_service.py    # parcourt le repo cloné pour trouver les fichiers
      docs_issue_service.py      # anciennes logiques docs V1 (optionnel)
      preprocessing_model.py     # PreprocessingModelIssuesV2, PreprocessingModelFilesV2
      stm32cube_preprocessing_heuristics.py
    utils/
      paths.py    # DATA_DIR, chemins de config, etc.

  test/
    test_stats_issues_v2.py
    test_stats_files_v2.py
    test_tfidf_search_issues_v2.py
    test_tfidf_search_files_v2.py

  docs/ (à compléter)
    ... (documentation d’architecture, JSON schema, évaluation, etc.)
4. Prétraitement V2 pour les issues GitHub
4.1. Ingestion et nettoyage
github_service.py / fetch_issues.py :

Utilise l’API GitHub,
récupère toutes les issues (sans les PR),
enregistre dans raw_issues_<repo>.json.
clean_issues.py + cleaning_service.py :

Nettoie le texte :

normalisation des sauts de ligne,
suppression de certains artefacts, backticks, etc.
conversion des images en placeholder [IMAGE ATTACHED] + liste d’URLs.
Construit clean_text structuré :

text
Title: ...
Body:
...
Comments:
[author - date]
comment...
Produit clean_issues_<repo>.json.

4.2. PreprocessingModelIssuesV2
Implémenté dans preprocessing_model.py, s’appuie sur des heuristiques dans stm32cube_preprocessing_heuristics.py.

Pour chaque issue nettoyée, process_clean_issue(issue) produit un doc V2 :

json
{
  "id": "stm32cubeh7-issue-338",
  "source_kind": "issue",
  "repo": "STM32CubeH7",
  "mcu_package": "STM32CubeH7",
  "mcu_series": "H7",
  "type": "issue",
  "path": null,
  "github_url": "https://github.com/STMicroelectronics/STM32CubeH7/issues/338",
  "board": "STM32H743VITX",
  "category": null,
  "component": "ADC",
  "example_name": null,
  "issue_number": 338,
  "issue_title": "[Bug]: ...",
  "state": "open",
  "labels": ["bug"],
  "is_confirmed_bug": true,
  "created_at": "...",
  "closed_at": null,
  "ingest_version": "v2.0",
  "clean_text": "Title: ...",
  "image_urls": [],
  "images_count": 0,
  "is_valid": true,
  "layer": "CubeMX",
  "severity": "medium",
  "issue_kind": "bug_report",
  "related_issue_ids": []   // ajouté plus tard dans V2_sim
}
Heuristiques principales :
is_valid :

false si texte trop court,
false si labels “invalid”, “duplicate”, “wontfix”.
issue_kind (function classify_issue_kind) :

bug_report si label “bug” ou texte typique,
usage_question pour “how to / how do I / question”,
configuration_help si “configuration / configure / clock configuration”,
sinon other.
layer (function detect_layer) :

"HAL" si HAL_ ou “HAL driver”,
"LL" si LL_ ou “Low Layer”,
"Middleware" si LWIP, FATFS, FreeRTOS, USB Host/Device, etc.,
"CubeMX" si CubeMX, STM32CubeMX, MX_, etc.,
"Other" sinon.
severity (function detect_severity) :

low : doc/typo/cosmetic (labels doc/typo, mots documentation, typo, etc.),
high : mots associés à crash/blocage :
hardfault, crash, freeze, hang, stuck, blocking, deadlock,
data corruption, doesn't start, no communication, watchdog reset, etc.,
medium sinon.
Cas particulier traité : “No response” dans les templates n’est plus pris comme high.
board (function detect_board) :

regex sur NUCLEO-[A-Z0-9]+, STM32H7[0-9A-Z]+, STM32F4..., etc., dans le texte.
component (function detect_component) :

liste de keywords associés à ETH, USB, ADC, DMA, UART, CAN, FreeRTOS, etc.
4.3. Similarité entre issues (TF‑IDF, V2_sim)
compute_issue_similarity_v2.py :
Lit docs_issues_<repo>_v2.json,

Garde seulement is_valid == true,

Construit un TF‑IDF sur issue_title + clean_text,

Calcule cosine_similarity,

Pour chaque issue valide, ajoute :

json
"related_issue_ids": ["stm32cubeh7-issue-120", "stm32cubeh7-issue-85", ...]
Enregistre dans docs_issues_<repo>_v2_sim.json en conservant tous les champs de V2.

4.4. Chunking des issues (V2)
docs_to_chunks_issues_v2.py :
Lit docs_issues_<repo>_v2_sim.json (ou _v2.json),

Ignore is_valid == false,

Découpe clean_text en plusieurs chunks par paragraphes (taille max ~1200 caractères),

Produit chunks_issues_<repo>_v2.json :

json
{
  "id": "stm32cubeh7-issue-338-0",
  "text": "portion de clean_text...",
  "metadata": {
    "source_kind": "issue",
    "repo": "STM32CubeH7",
    "mcu_series": "H7",
    "issue_number": 338,
    "issue_title": "...",
    "github_url": "...",
    "board": "STM32H743VITX",
    "component": "ADC",
    "layer": "CubeMX",
    "severity": "medium",
    "issue_kind": "bug_report",
    "related_issue_ids": [...],
    "is_valid": true,
    "chunk_index": 0,
    "chunk_count": 3,
    "ingest_version": "v2.0"
  }
}
5. Prétraitement V2 pour les fichiers (README / Release Notes / Projects)
5.1. Nettoyage des fichiers
fetch_files.py + file_collect_service.py :

Parcourt le repo Git cloné (GitHub_repos/STM32CubeH7),

Récupère :

README racine,
README de projets (Projects/**/README*),
Release Notes, etc.,
Enregistre dans raw_files_<repo>.json :

json
{
  "repo": "STM32CubeH7",
  "path": "Projects/NUCLEO-H743ZI/Examples/ETH/ETH_BasicTxRx/README.md",
  "content": "...",
  "encoding": "utf-8"
}
clean_files.py :

Normalise les fins de lignes, strip(),

Détermine file_type via detect_file_type(path) :

release_notes, project_readme, root_readme, doc_readme, other,
Produit clean_files_<repo>.json :

json
{
  "repo": "STM32CubeH7",
  "path": "README.md",
  "clean_text": "...",
  "file_type": "root_readme",
  "encoding": "utf-8"
}
5.2. PreprocessingModelFilesV2
Dans preprocessing_model.py :

json
{
  "id": "stm32cubeh7-file-6606534015442931394",
  "source_kind": "file",
  "repo": "STM32CubeH7",
  "mcu_package": "STM32CubeH7",
  "mcu_series": "H7",
  "type": "file",
  "path": "README.md",
  "file_type": "root_readme",
  "github_url": null,
  "board": "NUCLEO-H7A3ZI",
  "category": null,
  "component": "USB",
  "example_name": null,
  "ingest_version": "v2.0",
  "clean_text": "... (contenu du README) ...",
  "is_valid": true
}
Heuristiques :

board : detect_board(path + clean_text) → ex : NUCLEO-H7A3ZI dans la liste “Boards available”.
component : detect_component, ex. USB car README mentionne “USB” dans la liste des middlewares.
example_name : détecté dans Projects/.../Examples/<ExampleName>/... pour les README de projets.
is_valid : texte suffisamment long.
5.3. Chunking des fichiers
docs_to_chunks_files_v2.py :
Lit docs_files_<repo>_v2.json,
Applique un chunking par sections / paragraphes,
Produit chunks_files_<repo>_v2.json avec métadonnées héritées (file_type, board, component, example_name, etc.).
6. Scripts de tests & évaluation (sans LLM)
6.1. Scripts de stats (sanity checks)
test_stats_issues_v2.py :

lit docs_issues_<repo>_v2.json,
affiche :
distribution de layer, severity, issue_kind,
top board, component.
test_stats_files_v2.py :

lit docs_files_<repo>_v2.json,
affiche :
distribution de file_type,
proportion de is_valid,
top board, component.
6.2. Cohérence V2 vs V2_sim
test_consistency_issues_v2_vs_sim.py :
vérifie que pour chaque id, les champs clés (layer, severity, issue_kind, etc.) sont identiques entre docs_issues_v2 et docs_issues_v2_sim,
seule différence : la présence de related_issue_ids en V2_sim.
6.3. Recherche TF‑IDF sur issues / fichiers
test_tfidf_search_issues_v2.py :

construit un TF‑IDF sur issue_title + clean_text des issues valides,
boucle interactive : l’utilisateur tape une question, le script affiche les top‑k issues les plus proches (score, issue_number, layer, severity, board, component, url).
test_tfidf_search_files_v2.py :

TF‑IDF sur path + [file_type] + clean_text des fichiers valides,
top‑k fichiers pertinents avec affichage de file_type, path, board, component, example_name + extrait du texte.
Ces scripts servent à une évaluation qualitative du prétraitement V2, en montrant que :

les problèmes typiques (ex : bug CubeMX ADC/DMA) remontent bien,
les README/Release Notes pertinents sont retrouvés pour des questions globales (ex : “How to clone STM32CubeH7 repository with submodules”).
7. PC hors domaine & IA “complète”
Sur le PC ST, tu étais limité (pas de clé OpenAI, Ollama bloqué par proxy).
Sur le PC hors domaine :

Tu pourras, si tu veux, ajouter une couche RAG complète par dessus ce pipeline :
embeddings (OpenAI, ollama, sentence-transformers, etc.),
index vectoriel (FAISS/Chroma),
LLM pour la génération,
et évaluer l’impact de V2 sur la qualité des réponses.
Ce pipeline Python V2 (issues + fichiers + stats + TF‑IDF) est donc la base de données structurée et annotée sur laquelle tu peux brancher un RAG complet, sans devoir réinventer tout l’ingestion / prétraitement sur le nouveau PC.

Tu peux donner ce texte brut à l’autre assistant IA sur ton PC hors domaine.
Il aura ainsi :

la vision globale du PFE,
les fichiers clés,
les formats JSON,
la logique de prétraitement V2,
et le contexte de tests/évaluation,
pour t’aider à construire un RAG complet, une UI, ou à améliorer encore les heuristiques avec des LLM.
