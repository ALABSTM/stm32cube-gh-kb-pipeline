# Presentation Workflow STM32Cube Preprocessing Agent

## Slide 1 - Titre
Workflow STM32Cube Preprocessing Agent
De la collecte GitHub au corpus RAG pret a l integration

## Slide 2 - Probleme et objectif
- Problematique: data GitHub heterogene et volumineuse
- Objectif: generer des documents enrichis, fiables et exploitables pour RAG
- Positionnement agent: orchestration, qualite, documentation

## Slide 3 - Vue d ensemble
- Ingestion issues et fichiers
- Cleaning
- Enrichissement V2
- Similarite issues
- Chunking conditionnel
- Evaluation qualite

## Slide 4 - Etapes techniques
1. fetch_issues.py et fetch_files.py
2. clean_issues.py et clean_files.py
3. issues_to_docs_v2.py et files_to_docs_v2.py
4. compute_issue_similarity_v2.py
5. docs_to_chunks_issues_v2.py et docs_to_chunks_files_v2.py

## Slide 5 - Role de l agent
- Verifier coherence du pipeline
- Interpreter layer, severity, issue_kind, board, component
- Identifier les biais de preprocessing
- Produire documentation exploitable projet/PFE

## Slide 6 - Etat d avancement
- H7 issues: complet
- H7 fichiers: complet
- H5 issues: complet
- H5 fichiers: a completer
- Progression globale: 77.8%

## Slide 7 - Validation qualite
- Stats distributions: test_stats_issues_v2.py, test_stats_files_v2.py
- Retrieval TF-IDF: test_tfidf_search_issues_v2.py, test_tfidf_search_files_v2.py
- But: valider la pertinence avant embeddings/vector DB

## Slide 8 - Entree recommandee pour ST RAG
Si ST fait le chunking:
- utiliser docs_issues_<repo>_v2.json
- utiliser docs_files_<repo>_v2.json
- ne pas injecter chunks_<...>_v2.json pour eviter double chunking

## Slide 9 - Prochaines actions
1. Completer pipeline fichiers H5
2. Construire benchmark de requetes metier
3. Comparer retrieval TF-IDF et retrieval embeddings

## Slide 10 - Conclusion
Le pipeline V2 est deja solide sur les issues et sur les fichiers H7.
La priorite immediate est de fermer le gap fichiers H5 puis de normaliser l evaluation retrieval.
