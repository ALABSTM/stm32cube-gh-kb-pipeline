# Workflow STM32Cube Preprocessing Agent

## 1. Objectif
Ce document presente un workflow simple a expliquer et detaille a executer pour transformer les donnees STM32Cube en corpus pret pour un systeme RAG.

Le point central est l agent STM32Cube Preprocessing Agent, qui ne fait pas seulement l execution des scripts:
- il structure le flux de donnees,
- il controle la qualite des artefacts,
- il documente les choix heuristiques,
- il aide a l evaluation avant integration RAG finale.

## 2. Pipeline complet

### Etape A. Ingestion Issues GitHub
- Script: src/scripts/fetch_issues.py
- Service: src/services/github_service.py
- Entree: owner + repos dans src/config/config.json
- Sortie: data/raw_issues_<repo>.json
- But: recuperer toutes les issues open et closed + commentaires

### Etape B. Ingestion Fichiers des repos clones
- Script: src/scripts/fetch_files.py
- Service: src/services/file_collect_service.py
- Entree: dossiers locaux GitHub_repos/<Repo>
- Sortie: data/raw_files_<repo>.json
- But: collecter README, Release Notes, docs Projects

### Etape C. Nettoyage Issues
- Script: src/scripts/clean_issues.py
- Service: src/services/cleaning_service.py
- Sortie: data/clean_issues_<repo>.json
- But: normaliser le texte, remplacer balises image, fusionner body + commentaires

### Etape D. Nettoyage Fichiers
- Script: src/scripts/clean_files.py
- Sortie: data/clean_files_<repo>.json
- But: normaliser texte + classifier file_type

### Etape E. Enrichissement V2 Issues
- Script: src/scripts/issues_to_docs_v2.py
- Services: src/services/preprocessing_model.py + src/services/stm32cube_preprocessing_heuristics.py
- Sortie: data/docs_issues_<repo>_v2.json
- Champs cles: layer, severity, issue_kind, board, component, is_valid

### Etape F. Enrichissement V2 Fichiers
- Script: src/scripts/files_to_docs_v2.py
- Service: src/services/preprocessing_model.py
- Sortie: data/docs_files_<repo>_v2.json
- Champs cles: file_type, board, component, example_name, is_valid

### Etape G. Similarite entre issues
- Script: src/scripts/compute_issue_similarity_v2.py
- Sortie: data/docs_issues_<repo>_v2_sim.json
- But: ajouter related_issue_ids via TF-IDF + similarite cosinus

### Etape H. Chunking
- Issues: src/scripts/docs_to_chunks_issues_v2.py
- Fichiers: src/scripts/docs_to_chunks_files_v2.py
- Service: src/services/chunk_service.py
- Sorties: data/chunks_issues_<repo>_v2.json et data/chunks_files_<repo>_v2.json
- But: decoupage multi paragraphes avec metadata complete

Important pour ton cas:
Si l outil RAG ST fait lui meme le chunking, on utilise directement docs_issues_<repo>_v2.json et docs_files_<repo>_v2.json comme entree, et pas les fichiers chunks.

## 3. Schema resume du pipeline

[GitHub API Issues] + [Repos locaux STM32Cube]
                |
                v
       Ingestion (fetch_issues, fetch_files)
                |
                v
        Raw JSON (raw_issues, raw_files)
                |
                v
      Cleaning (clean_issues, clean_files)
                |
                v
      Clean JSON (clean_issues, clean_files)
                |
                v
 Enrichissement V2 (issues_to_docs_v2, files_to_docs_v2)
                |
                v
      Docs V2 (metadata + clean_text + is_valid)
                |
                +----> Similarite Issues V2 (related_issue_ids)
                |
                +----> Chunking V2 (si necessaire)
                |
                v
   Entree RAG ST recommandee: docs_issues_v2 + docs_files_v2

## 4. Etat d avancement actuel

### 4.1 Artefacts presents
- H7 Issues: raw, clean, docs_v2, docs_v2_sim, chunks_v2 disponibles
- H7 Fichiers: raw, clean, docs_v2, chunks_v2 disponibles
- H5 Issues: raw, clean, docs_v2, docs_v2_sim, chunks_v2 disponibles
- H5 Fichiers: artefacts V2 fichiers absents

### 4.2 Taux global
- Artefacts attendus sur 2 repos (issues + fichiers): 18
- Artefacts actuellement presents: 14
- Progression globale estimee: 77.8%

### 4.3 Tests qualite disponibles
- src/test/test_stats_issues_v2.py
- src/test/test_stats_files_v2.py
- src/test/test_tfidf_search_issues_v2.py
- src/test/test_tfidf_search_files_v2.py

## 5. Evaluation et validation qualite

### 5.1 Validation statistique
Scripts:
- src/test/test_stats_issues_v2.py
- src/test/test_stats_files_v2.py

Objectif:
- verifier les distributions layer, severity, issue_kind, file_type, board, component,
- verifier le ratio de documents valides,
- detecter biais de classification.

Interpretation attendue:
- trop de Other dans layer -> heuristiques a enrichir,
- trop de high dans severity -> seuils ou mots cles trop aggressifs,
- board/component souvent vides -> regex de detection a renforcer.

### 5.2 Validation retrieval pre RAG (TF-IDF)
Scripts:
- src/test/test_tfidf_search_issues_v2.py
- src/test/test_tfidf_search_files_v2.py

Objectif:
- verifier que les documents sont recuperables de facon pertinente avant embeddings vectoriels,
- controler que les top resultats correspondent bien aux requetes techniques.

Lecture des resultats:
- un top 5 pertinent sur plusieurs requetes metier indique que le preprocessing conserve bien le signal utile,
- des resultats hors sujet indiquent souvent un probleme de cleaning, de filtrage ou de metadata.

## 6. Recommandations immediate pour integration ST RAG
1. Envoyer en entree prioritaire:
   - data/docs_issues_stm32cubeh7_v2.json
   - data/docs_files_stm32cubeh7_v2.json
   - data/docs_issues_stm32cubeh5_v2.json
2. Optionnel:
   - data/docs_issues_stm32cubeh7_v2_sim.json
   - data/docs_issues_stm32cubeh5_v2_sim.json
3. Filtrer is_valid = true avant ingestion.
4. Garder metadata utiles: repo, mcu_series, layer, severity, issue_kind, board, component, file_type.

## 7. Plan d action court terme
1. Completer la branche fichiers H5 (raw_files, clean_files, docs_files_v2, chunks_files_v2).
2. Lancer les stats H7 et H5 et archiver les sorties dans docs/evaluation_results.md.
3. Construire une liste de 20 requetes metier STM32 pour benchmark retrieval reproductible.

## 8. Export PDF
- Ouvrir ce fichier markdown dans VS Code.
- Utiliser la fonction Export to PDF de l extension Markdown PDF, ou impression PDF via preview markdown.
- Nom conseille: Workflow_STM32Cube_Preprocessing_Agent.pdf
