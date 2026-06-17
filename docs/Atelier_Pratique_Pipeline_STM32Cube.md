# Atelier Pratique — Pipeline de Prétraitement STM32Cube

## Objectif

Ce guide permet à l'équipe de **lancer, comprendre et maintenir** le pipeline de prétraitement de bout en bout :  
**Ingestion → Cleaning → Enrichment → Similarity → Delivery → Alfred → Upload KB**

---

## 1. Prérequis

### 1.1 Environnement

```powershell
# Cloner le repo
git clone https://github.com/abirGharbi-st/PFE_Chatbot_STM32Cube.git
cd PFE_Chatbot_STM32Cube

# Créer le venv Python 3.11+
python -m venv .venv
.venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt
```

### 1.2 Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `GITHUB_TOKEN` | Token GitHub avec accès aux repos STMicroelectronics | `ghp_xxxx...` |
| `STM32CUBE_CONFIG` | (Optionnel) Chemin vers un config spécifique | `shared/config/config_f7.json` |

```powershell
$env:GITHUB_TOKEN = "ghp_votre_token"
```

### 1.3 Structure du projet

```
PFE_Chatbot_STM32Cube/
├── shared/config/          # Fichiers de config par série (config_h7.json, config_f4.json...)
├── pipeline/               # Code du pipeline (ingestion, cleaning, enrichment, etc.)
├── pipeline_Automation/    # Scripts Alfred + Upload KB
├── data/                   # Fichiers intermédiaires (raw, clean, docs, chunks)
├── datasets/07_delivery/   # Outputs finaux ST-ready
└── GitHub_repos/           # Clones locaux des repos (auto-créés)
```

---

## 2. Configuration d'une série

Chaque série STM32 a un fichier de config sous `shared/config/config_<serie>.json` :

```json
{
  "owner": "STMicroelectronics",
  "repos": [
    "STM32CubeH7",           // Repo principal
    "stm32h7xx-hal-driver",  // Sous-repos (drivers)
    "cmsis_device_h7",
    "stm32h7xx-nucleo-bsp"
  ],
  "data_dir": "data",
  "repos_dir": "GitHub_repos",
  "auto_clone_missing_repos": true,
  "repo_clone_urls": { ... },
  "github_token_env": "GITHUB_TOKEN",
  "rate_limits": {
    "issues_sleep": 0.2,
    "comments_sleep": 0.1
  }
}
```

**Pour ajouter une nouvelle série :**
1. Créer `shared/config/config_<serie>.json` avec la liste des repos
2. Ajouter le mapping des sous-repos dans `pipeline/delivery/delivery_paths.py`
3. Lancer le pipeline

---

## 3. Exécution du Pipeline

### 3.1 Workflow complet (une série)

```powershell
$env:STM32CUBE_CONFIG = "shared/config/config_h7.json"
python -m pipeline.run_full_workflow --export-st-ready --continue-on-error
```

**Options :**
| Flag | Effet |
|------|-------|
| `--export-st-ready` | Génère les JSON de delivery après le pipeline |
| `--continue-on-error` | Ne s'arrête pas si un step échoue |
| `--skip-ingestion` | Saute l'ingestion (utilise les raw existants) |
| `--skip-chunking` | Saute le chunking local |
| `--no-enrich-pdf` | Saute l'enrichissement Alfred des figures PDF |

### 3.2 Étapes du pipeline (dans l'ordre)

| # | Étape | Script | Input → Output |
|---|-------|--------|----------------|
| 1 | Ingestion Issues | `fetch_issues.py` | GitHub API → `data/raw_issues_<repo>.json` |
| 2 | Ingestion PRs | `fetch_prs.py` | GitHub API → `data/raw_prs_<repo>.json` |
| 3 | Ingestion Commits | `fetch_commits.py` | GitHub API → `data/raw_commits_<repo>.json` |
| 4 | Ingestion Links | `fetch_issue_pr_commit_links.py` | Croisement issues/PRs/commits |
| 5 | Sync repos | `repo_sync_service.py` | Clone/pull les repos localement |
| 6 | Ingestion Files | `fetch_files.py` | Repos locaux → `data/raw_files_<repo>.json` |
| 7 | Alfred PDF | `enrich_pdf_figures_with_alfred.py` | Figures PDF → descriptions texte |
| 8 | Cleaning Issues | `clean_issues.py` | raw → `data/clean_issues_<repo>.json` |
| 9 | Cleaning Files | `clean_files.py` | raw → `data/clean_files_<repo>.json` |
| 10 | Enrichment Issues | `issues_to_docs_v2.py` | clean → `data/docs_issues_<repo>_v2.json` |
| 11 | Enrichment Files | `files_to_docs_v2.py` | clean → `data/docs_files_<repo>_v2.json` |
| 12 | Similarity | `compute_issue_similarity_v2.py` | docs → `data/docs_issues_<repo>_v2_sim.json` |
| 13 | Chunking Issues | `docs_to_chunks_issues_v2.py` | docs → `data/chunks_issues_<repo>_v2.json` |
| 14 | Chunking Files | `docs_to_chunks_files_v2.py` | docs → `data/chunks_files_<repo>_v2.json` |
| 15 | Stats + Validation | `test_stats_*.py` + `validate_schemas.py` | Vérification qualité |
| 16 | Delivery | `export_st_ready_*.py` | → `datasets/07_delivery/st_ready/by_series/` |

### 3.3 Lancer plusieurs séries

```powershell
foreach ($serie in @("config_c0", "config_f0", "config_f1", "config_f2", "config_f3", "config_f7", "config_g0", "config_h7rs")) {
    Write-Host "=== Processing $serie ===" -ForegroundColor Cyan
    $env:STM32CUBE_CONFIG = "shared/config/$serie.json"
    python -m pipeline.run_full_workflow --export-st-ready --continue-on-error --no-enrich-pdf
}
```

---

## 4. Enrichissement Alfred (Images)

### 4.1 Images dans les issues (captures d'écran)

Alfred Vision analyse les captures d'écran attachées aux issues et remplace `[IMAGE ATTACHED]` par `[IMAGE DESCRIPTION] ...`

```powershell
python pipeline_Automation/alfred/enrich_json_images_with_alfred.py `
  --input "datasets/07_delivery/st_ready/by_series/stm32cubeh7/issues_json/st_ready_issues_with_images_stm32cubeh7.json" `
  --inplace --use-proxy
```

**Le fichier résultant** : `st_ready_issues_with_images_<repo>_with_alfred_image_text.json`

> ⚠️ Seules les séries avec des images dans les issues ont un fichier `with_images`. Si le fichier n'existe pas, la série n'a pas d'images → pas besoin d'Alfred.

### 4.2 Figures PDF

Alfred Vision décrit les figures extraites des PDFs techniques :

```powershell
python pipeline_Automation/alfred/enrich_pdf_figures_with_alfred.py --repo STM32CubeH7 --use-proxy
```

### 4.3 Séries avec images (à ce jour)

| Série | Issues avec images | Alfred requis |
|-------|:--:|:--:|
| H7 | 53 | ✅ |
| F4 | 34 | ✅ |
| WL | 23 | ✅ |
| U5 | 6 | ✅ |
| H5 | 3 | ✅ |
| C0, F0-F3, F7, G0, H7RS | 0 | ❌ |

---

## 5. Upload vers la Knowledge Base

### 5.1 Architecture de la KB

La KB **#793** (ST GitHub Analyzer) contient des **datasources séparées par série ET par type** :

```
KB #793
├── STM32H7 Issues (#24406)
├── STM32H7 Files (#29041)
├── STM32H7 Diagnostic Cards (#24408)
├── STM32H7 Resolver Cases (#24410)
├── STM32F4 Issues (#28099)
├── STM32F4 Files (#29042)
├── ...
```

### 5.2 Processor params (4 types)

| Type | rootTagPath | Label template |
|------|-------------|---------------|
| Issues | `issues` | `{{repo}} issue #{{issue_number}} - {{issue_title}}` |
| Files | `files` | `{{repo}} {{file_type}} - {{path}}` |
| Resolver Cases | `resolver_cases` | `{{label}}` |
| Diagnostic Cards | — | `{{label}}` |

### 5.3 Créer une nouvelle datasource

```powershell
$paramsIssues = '{"label": "{{repo}} issue #{{issue_number}} - {{issue_title}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/issues/{{issue_number}}", "rootTagPath": "issues"}'
$b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($paramsIssues))

python pipeline_Automation/upload/Add_Data_Source_Files.py `
  --kb 793 --operation new `
  --datasource-name "STM32XX Issues" `
  --remote-user "votre.email@st.com" --processor JSON `
  --processor-params "base64:$b64" --json-split-size 1000 `
  --files "datasets/07_delivery/st_ready/by_series/stm32cubexx/issues_json/st_ready_issues_stm32cubexx.json"
```

### 5.4 Ajouter des fichiers à une datasource existante

```powershell
python pipeline_Automation/upload/Add_Data_Source_Files.py `
  --kb 793 --operation add --datasource-id <ID> `
  --remote-user "votre.email@st.com" --processor JSON `
  --processor-params "base64:$b64" --json-split-size 1000 `
  --files "chemin/vers/fichier.json"
```

### 5.5 Upload des drivers (automatisé)

```powershell
.\pipeline_Automation\upload\Upload_All_Drivers.ps1
```

Ce script :
- Scanne tous les `by_series/<serie>/drivers/` 
- Route chaque artifact vers la bonne datasource (issues → DS Issues, files → DS Files...)
- Ignore les fichiers vides
- Affiche un résumé

### 5.6 Vérifier le contenu de la KB

```powershell
python pipeline_Automation/upload/Get_Persona_KBs.py
```

---

## 6. Bonnes Pratiques

### 6.1 Exécution

| Règle | Pourquoi |
|-------|----------|
| Toujours utiliser `--continue-on-error` | Un sous-repo sans issues ne doit pas bloquer les autres |
| Vérifier les `summary_*.json` après delivery | Confirme les counts avant upload |
| Ne pas uploader les fichiers vides (`[]`) | L'API rejecte avec "empty JSON arrays" |
| Utiliser `--skip-ingestion` pour re-processer | Évite de re-télécharger les issues (rate limit GitHub) |

### 6.2 Organisation des datasources

| Règle | Pourquoi |
|-------|----------|
| 1 datasource = 1 série + 1 type d'artifact | Permet le remplacement ciblé |
| Les drivers vont dans la MÊME datasource que le repo principal | Même série = même contexte |
| Nommage : `STM32XX <Type>` | Lisibilité dans KB Management |

### 6.3 Alfred

| Règle | Pourquoi |
|-------|----------|
| `--use-proxy` sur le réseau ST | Proxy obligatoire pour api-ai-bridge.st.com |
| `--inplace` pour remplacer le fichier | Évite les doublons |
| Vérifier 0 `[IMAGE DESCRIPTION UNAVAILABLE]` | Si présent = URL expirée ou rate limit |

### 6.4 Git

| Règle | Pourquoi |
|-------|----------|
| Ne JAMAIS commit les fichiers `data/*.json` | Dépassent 100 MB → push rejeté |
| Le `.gitignore` exclut `data/raw_*`, `data/clean_*`, `data/docs_*`, `data/chunks_*` | Protection automatique |
| Les `datasets/07_delivery/` sont committés | Ils sont plus petits et représentent le livrable |

---

## 7. Workflow complet — Nouvelle série (checklist)

```
□ 1. Créer shared/config/config_<serie>.json
□ 2. Ajouter le mapping sous-repos dans pipeline/delivery/delivery_paths.py
□ 3. Lancer: $env:STM32CUBE_CONFIG = "shared/config/config_<serie>.json"
             python -m pipeline.run_full_workflow --export-st-ready --continue-on-error
□ 4. Vérifier datasets/07_delivery/st_ready/by_series/stm32cube<serie>/
     - issues_json/ ✓
     - files_json/ ✓
     - diagnostic_cards_json/ ✓
     - resolver_cases_json/ ✓
     - drivers/ (si sous-repos) ✓
□ 5. Alfred (si images): 
     python pipeline_Automation/alfred/enrich_json_images_with_alfred.py --input <with_images.json> --inplace --use-proxy
□ 6. Upload repo principal (4 commandes: issues, files, diag, resolver)
□ 7. Upload drivers: .\pipeline_Automation\upload\Upload_All_Drivers.ps1
□ 8. Vérifier: python pipeline_Automation/upload/Get_Persona_KBs.py
```

---

## 8. Dépannage

| Problème | Cause | Solution |
|----------|-------|----------|
| `FileNotFoundError: st_ready_issues_with_images_*.json` | La série n'a pas d'images | Normal — skip Alfred images |
| `ValueError: All selected files are empty JSON arrays` | Pas de resolver cases | Normal — série sans fix documenté |
| `Datasource response: skipped_existing_files` | Fichier déjà uploadé | Supprimer le fichier dans KB Management puis re-uploader, ou créer un nouveau datasource |
| `error: File exceeds GitHub's file size limit` | Fichier `data/*.json` > 100 MB dans git | Vérifier `.gitignore` exclut bien `data/` |
| `rate limit` GitHub | Trop d'appels API | Attendre 1h ou augmenter `issues_sleep` dans config |
| Enrichment 0% pour un sous-repo | Pas de `docs_issues_*_v2.json` | Normal — les sous-repos BSP ont peu d'issues |

---

## 9. Contacts et Ressources

- **API Alfred Vision** : `api-ai-bridge.st.com` / client `mdrf_stgithub_analyzer_client`
- **KB Management** : Interface web ST ChatGPT → Knowledge Bases → #793
- **Persona** : "ST GitHub Analyzer" / client `mdrf_st_github_analyzer`
- **Repo GitHub** : `github.com/abirGharbi-st/PFE_Chatbot_STM32Cube`
