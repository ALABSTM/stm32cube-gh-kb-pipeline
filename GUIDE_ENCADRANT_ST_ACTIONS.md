# Guide Encadrant ST - Execution GitHub Actions

## Objectif
Ce guide permet d'executer et valider l'automatisation STM32Cube sur le depot ST, avec un ordre de tests fiable et une checklist claire.

## Contexte de run
- Depot: STM32_ChatBOT_DataPipeline
- Branche cible: PFE_Chatbot_STM32Cube_V2
- KB cible: 793

---

## 1) Checklist prerequis

### 1.1 Acces et repository
- [ ] GitHub Actions active sur le repo
- [ ] Droit Write ou Maintainer
- [ ] Branche `PFE_Chatbot_STM32Cube_V2` visible

### 1.2 Workflows attendus
- [ ] `.github/workflows/smoke_test_st_api.yml`
- [ ] `.github/workflows/manual_auto_update_kb.yml`
- [ ] `.github/workflows/auto_update_kb.yml`

### 1.3 Secrets requis
- [ ] `RUNNER_CHECK_TOKEN`
- [ ] `ST_CHATGPT_API_KEY`
- [ ] `ST_GITHUB_ANALYZER_API_KEY`
- [ ] `ST_REMOTE_USER`


### 1.4 Runner (si mode self-hosted)
- [ ] Runner online + idle
- [ ] Python 3.12+
- [ ] Git LFS installe
- [ ] Connectivite vers `https://api-ai-bridge.st.com/chatgpt/api/client-apps`

---


## 2) Ordre exact des tests

### Test 1 - Smoke API
Workflow: `smoke_test_st_api.yml`
- [ ] Lancer en manuel
- [ ] Resultat attendu: acces API OK

### Test 2 - Prepare only
Workflow: `manual_auto_update_kb.yml`
Inputs:
- `series=C0`
- `mode=Prepare`
- `upload_execution_target=github-hosted` (ou self-hosted)
- `skip_schema_validation=false`
- `continue_on_workflow_error=false`

- [ ] Resultat attendu: generation des artefacts ST-ready sans echec

### Test 3 - Upload only
Workflow: `manual_auto_update_kb.yml`
Inputs recommandes:
- `series=C0`
- `mode=Upload`
- `existing_datasource_mode=Add`
- `enable_issues_by_component_flow=true`
- `component_issues_only=true`
- `upload_execution_target=self-hosted` (ou github-hosted)

- [ ] Resultat attendu: upload KB sans erreur auth

### Test 4 - Full
Workflow: `manual_auto_update_kb.yml`
Inputs recommandes:
- `series=C0`
- `mode=Full`
- `existing_datasource_mode=Add`
- `enable_issues_by_component_flow=true`
- `component_issues_only=true`
- `upload_execution_target=self-hosted` (ou github-hosted)

- [ ] Resultat attendu: preprocess + upload completes

---

## 3) Verification post-run
- [ ] Consulter les logs des etapes upload (issues/files/resolver)
- [ ] Verifier le registre datasource IDs:
  - `datasets/07_delivery/st_ready/by_series/stm32cubec0/upload_datasource_ids_stm32cubec0.json`
- [ ] Verifier absence de crash `JSONDecodeError`
- [ ] Verifier que les warnings toleres n'arretent pas le workflow

---

## 4) Incidents frequents

### Cas A - "please complete authentication in your browser"
Cause: SSO Git en attente
Action: terminer l'auth navigateur puis relancer la commande

### Cas B - "Uploading LFS objects ..."
Cause: transfert LFS en cours
Action: patienter; relancer si interruption

### Cas C - non-fast-forward au push
Cause: branche distante en avance / rebase en cours
Action: terminer ou abort la rebase, puis rebase propre et push

### Cas D - Upload auth precheck failed
Cause probable: secret manquant ou invalide
Action: verifier `ST_GITHUB_ANALYZER_API_KEY` et `ST_REMOTE_USER`

---

## 5) Validation finale
- [ ] Smoke OK
- [ ] Prepare C0 OK
- [ ] Upload C0 OK
- [ ] Full C0 OK
- [ ] Lien des runs archive
