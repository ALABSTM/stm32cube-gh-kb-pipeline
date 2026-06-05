# Pipeline Folder

This folder organizes code by pipeline stages.

- ingestion: source collection from GitHub API and local repos
- cleaning: text normalization and sanitization
- enrichment: metadata extraction and V2 document generation
- similarity: related issue linking
- chunking: optional chunk generation
- evaluation: stats and retrieval validation
- delivery: export preparation for ST RAG
