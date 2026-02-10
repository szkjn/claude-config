# Skill: Elasticsearch Search

Accès en lecture seule à l'index Elasticsearch de production Wisepipe.

## Configuration

- **Host:** variable `ELASTICSEARCH_HOST` dans `~/Code/claude-config/.env`
- **API key:** variable `ELASTICSEARCH_API_KEY_READONLY` dans `~/Code/claude-config/.env`
- **Index principal:** `wisepipe-all-3` (contient toutes les sources)

## Utilisation

Toutes les requêtes utilisent `curl` avec l'API key en header:

```bash
ES_API_KEY=$(grep ELASTICSEARCH_API_KEY_READONLY ~/Code/claude-config/.env | cut -d= -f2)
ES_HOST=$(grep ELASTICSEARCH_HOST ~/Code/claude-config/.env | cut -d= -f2)
```

### Recherche full-text

```bash
curl -s -H "Authorization: ApiKey $ES_API_KEY" \
  "$ES_HOST/wisepipe-all-3/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"match": {"content": "QUERY"}}, "size": 5, "_source": ["wisetax_id", "title", "corpus", "date"]}' | jq .
```

### Récupérer un document par ID perm

```bash
curl -s -H "Authorization: ApiKey $ES_API_KEY" \
  "$ES_HOST/wisepipe-all-3/_doc/IDENTIFIER_PERM" | jq ._source
```

### Rechercher par wisetax_id

```bash
curl -s -H "Authorization: ApiKey $ES_API_KEY" \
  "$ES_HOST/wisepipe-all-3/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"term": {"wisetax_id": "WISETAX_ID"}}, "size": 1}' | jq '.hits.hits[0]._source'
```

### Compter les documents par source (corpus)

```bash
curl -s -H "Authorization: ApiKey $ES_API_KEY" \
  "$ES_HOST/wisepipe-all-3/_search" \
  -H "Content-Type: application/json" \
  -d '{"size": 0, "aggs": {"by_corpus": {"terms": {"field": "corpus", "size": 50}}}}' | jq '.aggregations.by_corpus.buckets'
```

### Lister les index disponibles

```bash
curl -s -H "Authorization: ApiKey $ES_API_KEY" \
  "$ES_HOST/_cat/indices?v&h=index,docs.count,store.size" | sort
```

### Voir le mapping d'un index

```bash
curl -s -H "Authorization: ApiKey $ES_API_KEY" \
  "$ES_HOST/wisepipe-all-3/_mapping" | jq '.["wisepipe-all-3"].mappings.properties | keys'
```

## Index par source

| Source | Index |
|--------|-------|
| BOFIP, LEGI, JADE, CASS, WTDOC, CAPP, INCA, ARIANE, PDF, KALI | `wisepipe-all-3` |
| Documents externes (PDFs) | `wisepipe-060325` |

## Restrictions

- **Lecture seule** - uniquement GET et POST `_search` / `_count` / `_cat`
- Pas de POST `_index`, `_update`, `_delete`, `_bulk`
