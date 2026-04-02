# Demo Reelle - STM32Cube Preprocessing Agent

## Objectif

Cette demo montre que l'agent n'est pas un assistant generique: il sait lire les artefacts reels du pipeline STM32Cube, les interpreter, et produire une sortie exploitable pour la documentation, l'evaluation et la preparation d'un RAG.

## Format recommande

- Duree: 10 a 15 minutes
- Mode: ouvrir l'agent STM32Cube Preprocessing Agent dans VS Code
- Resultat attendu: montrer 3 usages complementaires des skills

## Fichiers a garder ouverts

- `.github/agents/STM32CubePreprocessing.agent.md`
- `.github/skills/analyze-stats/SKILL.md`
- `.github/skills/document-json-schema/SKILL.md`
- `.github/skills/chunking-strategies/SKILL.md`
- `data/docs_issues_stm32cubeh7_v2.json`
- `data/docs_files_stm32cubeh7_v2.json`
- `data/chunks_issues_stm32cubeh7_v2.json`

## Demo 1 - Montrer la comprehension metier d'un document V2

### Artefact reel utilise

Source: `data/docs_issues_stm32cubeh7_v2.json`

Objet reel a montrer: `stm32cubeh7-issue-339`

Extrait utile:

```json
{
  "id": "stm32cubeh7-issue-339",
  "repo": "STM32CubeH7",
  "component": "UART",
  "issue_number": 339,
  "issue_title": "[Bug]: USART with a single line",
  "state": "open",
  "is_confirmed_bug": true,
  "is_valid": true,
  "layer": "CubeMX",
  "severity": "medium",
  "issue_kind": "bug_report"
}
```

### Prompt a copier dans l'agent

```text
Analyse cet objet provenant de docs_issues_stm32cubeh7_v2.json.
Explique en termes STM32Cube ce que signifie chaque champ metier important, puis donne:
1. un resume fonctionnel de l'issue,
2. pourquoi is_valid=true est coherent ici,
3. comment ce document peut etre exploite dans un pipeline RAG technique.

Objet:
{
  "id": "stm32cubeh7-issue-339",
  "repo": "STM32CubeH7",
  "component": "UART",
  "issue_number": 339,
  "issue_title": "[Bug]: USART with a single line",
  "state": "open",
  "is_confirmed_bug": true,
  "is_valid": true,
  "layer": "CubeMX",
  "severity": "medium",
  "issue_kind": "bug_report"
}
```

### Valeur a verbaliser

- L'agent ne fait pas qu'expliquer du JSON.
- Il reconnecte les champs a la logique STM32Cube: couche logicielle, severite, validite, usage RAG.
- Il transforme un document technique en connaissance interpretable.

## Demo 2 - Montrer le skill document-json-schema

### Artefact reel utilise

Source: `data/docs_files_stm32cubeh7_v2.json`

Objet reel a montrer: `stm32cubeh7-file-3796368010915485190`

Extrait utile:

```json
{
  "id": "stm32cubeh7-file-3796368010915485190",
  "source_kind": "file",
  "repo": "STM32CubeH7",
  "path": "README.md",
  "file_type": "root_readme",
  "board": "NUCLEO-H7A3ZI",
  "component": "USB",
  "example_name": null,
  "ingest_version": "v2.0",
  "is_valid": true
}
```

### Prompt a copier dans l'agent

```text
A partir de cet exemple provenant de docs_files_stm32cubeh7_v2.json, genere une mini documentation de schema orientee projet STM32Cube.
Je veux un resultat sous forme de tableau Markdown avec:
- champ,
- type probable,
- signification dans le pipeline,
- obligatoire ou optionnel.

Exemple:
{
  "id": "stm32cubeh7-file-3796368010915485190",
  "source_kind": "file",
  "repo": "STM32CubeH7",
  "path": "README.md",
  "file_type": "root_readme",
  "board": "NUCLEO-H7A3ZI",
  "component": "USB",
  "example_name": null,
  "ingest_version": "v2.0",
  "is_valid": true
}
```

### Valeur a verbaliser

- Le skill document-json-schema reduit l'ambiguite entre data engineering, evaluation et integration RAG.
- Il permet de formaliser rapidement un contrat de donnees lisible.

## Demo 3 - Montrer la valeur du chunking sur un cas reel

### Artefacts reels utilises

Source 1: `data/docs_issues_stm32cubeh7_v2.json`

Issue reelle: `stm32cubeh7-issue-338`

Source 2: `data/chunks_issues_stm32cubeh7_v2.json`

Chunks reels: `stm32cubeh7-issue-338-0` et `stm32cubeh7-issue-338-1`

Constat reel: l'issue ADC avec DMA a ete coupee en 2 chunks, un pour la description, un pour les commentaires.

### Prompt a copier dans l'agent

```text
Compare ce document source et ses chunks V2.
Explique si la strategie de chunking est adaptee a un usage RAG technique STM32Cube.
Je veux:
1. les benefices du decoupage actuel,
2. les risques potentiels de perte de contexte,
3. une recommandation concrete entre garder ce decoupage ou le modifier.

Document source:
- issue_title: [Bug]: CubeMx allows an invalid combination of parameters for ADC with DMA
- layer: CubeMX
- component: ADC
- severity: low
- issue_kind: bug_report

Chunk 0 resume:
- contient le Bug Summary, la Detailed Description et l'environnement

Chunk 1 resume:
- contient les commentaires et la reference interne ST
```

### Valeur a verbaliser

- Ici on montre que le chunking n'est pas juste un detail technique.
- L'agent peut juger si la segmentation preserve la recuperation d'information utile.
- C'est directement lie a la qualite future du RAG.

## Demo 4 - Montrer le skill analyze-stats sur la vraie pipeline

### Commande a lancer avant ou pendant la reunion

```bash
python -m pipeline.evaluation.test_stats_issues_v2
```

### Prompt a copier apres execution

```text
Analyse cette sortie de test_stats_issues_v2.py.
Je veux une synthese orientee evaluation qualite avec:
1. les distributions importantes,
2. les biais potentiels de preprocessing,
3. les 3 actions prioritaires a mener.

Voici la sortie console:
[COLLER ICI LA SORTIE]
```

### Valeur a verbaliser

- Le skill analyze-stats convertit un simple affichage console en decisions actionnables.
- On passe de la mesure brute a l'interpretation qualite.

## Slide de conclusion

Message final a dire:

> Le pipeline produit des artefacts. L'agent, lui, transforme ces artefacts en comprehension, en documentation et en recommandations. C'est cette couche d'exploitation intelligente qui apporte la valeur.

## Version tres courte si tu n'as que 5 minutes

1. Demo 1 pour montrer la comprehension metier.
2. Demo 2 pour montrer la generation de schema.
3. Demo 3 pour montrer l'impact sur la qualite RAG.

## Resultat attendu en reunion

- Les personnes techniques voient que l'agent comprend la structure du pipeline.
- Les encadrants voient un gain concret en analyse et en documentation.
- La valeur des skills apparait comme modulaire, specialisee et directement exploitable.