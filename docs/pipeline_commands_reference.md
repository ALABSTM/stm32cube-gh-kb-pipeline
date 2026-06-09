# Pipeline Commands Reference — STM32Cube Preprocessing

> Toutes les commandes sont à exécuter depuis la racine du projet.
> Remplacer `STM32CubeH7` par le repo cible si besoin.

---

## 1. Full Workflow (toutes les étapes)

```powershell
python -m pipeline.run_full_workflow
```

Avec export ST-ready :
```powershell
python -m pipeline.run_full_workflow --export-st-ready
```

Options utiles :
```powershell
python -m pipeline.run_full_workflow --skip-ingestion --continue-on-error
```

---

## 2. Ingestion (fetch depuis GitHub)

```powershell
python -m pipeline.ingestion.fetch_issues --repo STM32CubeH7
python -m pipeline.ingestion.fetch_prs --repo STM32CubeH7
python -m pipeline.ingestion.fetch_commits --repo STM32CubeH7
python -m pipeline.ingestion.fetch_files --repo STM32CubeH7
python -m pipeline.ingestion.fetch_issue_pr_commit_links --repo STM32CubeH7
```

---

## 3. Cleaning

```powershell
python -m pipeline.cleaning.clean_issues
python -m pipeline.cleaning.clean_files
```

---

## 4. Enrichment (V2)

```powershell
python -m pipeline.enrichment.issues_to_docs_v2
python -m pipeline.enrichment.files_to_docs_v2
```

---

## 5. Similarity

```powershell
python -m pipeline.similarity.compute_issue_similarity_v2
```

---

## 6. Chunking

```powershell
python -m pipeline.chunking.docs_to_chunks_issues_v2
python -m pipeline.chunking.docs_to_chunks_files_v2
```

---

## 7. Delivery (Export ST-Ready)

### Issues (avec champ image_urls)
```powershell
python -m pipeline.delivery.export_st_ready_issues_with_images --repo STM32CubeH7
```

### Issues (standard sans images)
```powershell
python -m pipeline.delivery.export_st_ready_issues --repo STM32CubeH7
```

### Files
```powershell
python -m pipeline.delivery.export_st_ready_files --repo STM32CubeH7
```

### Resolver Cases
```powershell
python -m pipeline.delivery.export_st_ready_resolver_cases --repo STM32CubeH7
```

### Diagnostic Cards
```powershell
python -m pipeline.delivery.export_st_ready_diagnostic_cards --repo STM32CubeH7
```

---

## 8. Alfred — Enrichissement images

```powershell
python pipeline_Automation/alfred/enrich_json_images_with_alfred.py --input "datasets/07_delivery/st_ready/by_series/stm32cubeh7/issues_json/st_ready_issues_with_images_stm32cubeh7.json" --inplace
```

Options :
- `--use-proxy` : utiliser le proxy ST (185.46.212.88:80)
- `--no-replace-text` : ne pas remplacer [IMAGE ATTACHED] dans le texte
- `--max-records N` : limiter à N records
- `--strip-analyses` : retirer les analyses détaillées

---

## 9. Upload vers KB (datasource)

### Commande générique
```powershell
$params = '{"label": "{{repo}} issue #{{issue_number}} - {{issue_title}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/issues/{{issue_number}}", "rootTagPath": "issues"}'
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($params))
python pipeline_Automation/upload/Add_Data_Source_Files.py --kb 793 --operation add --datasource-id <ID> --remote-user "abir.gharbi@st.com" --processor JSON --processor-params "base64:$b64" --json-split-size 1000 --files "<chemin_fichier.json>"
```

### H7 Issues (datasource #24406)
```powershell
$params = '{"label": "{{repo}} issue #{{issue_number}} - {{issue_title}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/issues/{{issue_number}}", "rootTagPath": "issues"}'
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($params))
python pipeline_Automation/upload/Add_Data_Source_Files.py --kb 793 --operation add --datasource-id 24406 --remote-user "abir.gharbi@st.com" --processor JSON --processor-params "base64:$b64" --json-split-size 1000 --files "datasets/07_delivery/st_ready/by_series/stm32cubeh7/issues_json/st_ready_issues_with_images_stm32cubeh7.json"
```

### Params pour Files
```powershell
$params = '{"label": "{{repo}} - {{file_type}} - {{path}}", "externalURL": "{{github_url}}", "rootTagPath": "files"}'
```

### Params pour Resolver Cases
```powershell
$params = '{"label": "{{repo}} resolver #{{issue_number}} - {{issue_title}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/issues/{{issue_number}}", "rootTagPath": "resolver_cases"}'
```

### Params pour Diagnostic Cards
```powershell
$params = '{"label": "{{card_id}} - {{card_title}}", "externalURL": "{{primary_issue_url}}", "rootTagPath": "diagnostic_cards"}'
```

---

## 10. Evaluation

### Rapport d'évaluation (avec PDF)
```powershell
python -m pipeline.evaluation.generate_evaluation_report --repo STM32CubeH7 --pdf
```

### Stats issues
```powershell
python -m pipeline.evaluation.test_stats_issues_v2
```

### Stats files
```powershell
python -m pipeline.evaluation.test_stats_files_v2
```

### TF-IDF search test (issues)
```powershell
python -m pipeline.evaluation.test_tfidf_search_issues_v2
```

### TF-IDF search test (files)
```powershell
python -m pipeline.evaluation.test_tfidf_search_files_v2
```

### Validation schemas
```powershell
python -m pipeline.evaluation.validate_schemas
```

---

## 11. Automation Scripts (PowerShell)

### Pipeline complet pour tous les repos
```powershell
.\pipeline_Automation\workflow\Run_Issues_Pipeline_For_All_Repos.ps1
```

### Diagnostic cards pour tous les repos
```powershell
.\pipeline_Automation\workflow\Generate_Diagnostic_Cards_For_All_Repos.ps1
```

### Upload batch ST-Ready
```powershell
.\pipeline_Automation\upload\Upload_STReady_New_Batch.ps1
```

### Full auto-update KB
```powershell
.\pipeline_Automation\workflow\Run_Full_Auto_Update_KB.ps1
```

---

## Datasources IDs connus

| Repo | Type | Datasource ID |
|------|------|:-------------:|
| STM32CubeH7 | Issues | 24406 |
| STM32CubeH7 | Issues (ancien) | 19896 |
| STM32CubeH5 | Issues | — |
| STM32CubeF4 | Files | — |

> KB #793 = ST GitHub Analyzer Knowledge Base
