---
name: utils-es-query
description: Search the Wisepipe Elasticsearch production index (readonly)
---

# Skill: Elasticsearch Search

Accès en lecture seule à l'index Elasticsearch de production Wisepipe.

## Configuration

- **Script:** `~/Code/claude-config/scripts/es-query.sh` - wrapper qui charge les credentials automatiquement
- **Index principal:** `wisepipe-all-3` (contient toutes les sources)

## Utilisation

Utiliser le script wrapper:

```bash
~/Code/claude-config/scripts/es-query.sh <endpoint> [json-body]
```

### Recherche full-text

```bash
~/Code/claude-config/scripts/es-query.sh "wisepipe-all-3/_search" \
  '{"query": {"match": {"content": "QUERY"}}, "size": 5, "_source": ["wisetax_id", "title", "corpus", "date"]}' | jq .
```

### Récupérer un document par ID perm

```bash
~/Code/claude-config/scripts/es-query.sh "wisepipe-all-3/_doc/IDENTIFIER_PERM" | jq ._source
```

### Rechercher par wisetax_id

```bash
~/Code/claude-config/scripts/es-query.sh "wisepipe-all-3/_search" \
  '{"query": {"term": {"wisetax_id": "WISETAX_ID"}}, "size": 1}' | jq '.hits.hits[0]._source'
```

### Compter les documents par source (corpus)

```bash
~/Code/claude-config/scripts/es-query.sh "wisepipe-all-3/_search" \
  '{"size": 0, "aggs": {"by_corpus": {"terms": {"field": "corpus", "size": 50}}}}' | jq '.aggregations.by_corpus.buckets'
```

### Lister les index disponibles

```bash
~/Code/claude-config/scripts/es-query.sh "_cat/indices?v&h=index,docs.count,store.size" | sort
```

### Voir le mapping d'un index

```bash
~/Code/claude-config/scripts/es-query.sh "wisepipe-all-3/_mapping" \
  | jq '.["wisepipe-all-3"].mappings.properties | keys'
```

## Index par source

| Source | Index |
|--------|-------|
| BOFIP, LEGI, JADE, CASS, WTDOC, CAPP, INCA, ARIANE, PDF, KALI | `wisepipe-all-3` |
| Documents externes (PDFs) | `wisepipe-060325` |

## Restrictions

- **Lecture seule** - uniquement GET et POST `_search` / `_count` / `_cat`
- Pas de POST `_index`, `_update`, `_delete`, `_bulk`
