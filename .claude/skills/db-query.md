# Skill: Wisepipe Database Query

Accès en lecture seule à la base de données PostgreSQL de production Wisepipe.

## Configuration

- **Credentials:** Stockés dans `.env` (variables `CLAUDE_DB_*`)
- **Script:** `~/Code/claude-config/scripts/db-query.sh` - wrapper qui charge les credentials automatiquement
- **Schema:** `.claude/db-schema.md` - documentation complète des tables

## Utilisation

Exécuter des requêtes SQL en lecture seule:

```bash
~/Code/claude-config/scripts/db-query.sh "SELECT * FROM documents LIMIT 5;"
```

Mode interactif:

```bash
~/Code/claude-config/scripts/db-query.sh
```

## Tables disponibles

| Table | Description |
|-------|-------------|
| batches | Lots d'import de sources |
| documents | Documents indexés (table principale) |
| chunks | Fragments pour embeddings |
| links | Relations entre documents |
| external_docs | Documents externes (PDFs) |
| job_runs | Historique des jobs |
| manual_refs | Références manuelles |
| config | Configuration globale |
| summary_ratings | Évaluations des résumés |

## Requêtes utiles

```sql
-- Nombre de documents par type
SELECT type, COUNT(*) FROM documents GROUP BY type;

-- Documents récents
SELECT wisetax_id, type, status, created_at
FROM documents
ORDER BY created_at DESC LIMIT 10;

-- Chunks non embeddés
SELECT COUNT(*) FROM chunks WHERE embedded_v3 IS NOT TRUE;

-- Jobs en erreur
SELECT name, error, started_at FROM job_runs WHERE status = 'error';

-- Liens externes
SELECT * FROM links WHERE external = true LIMIT 10;
```

## Restrictions

- **Lecture seule** - pas de INSERT, UPDATE, DELETE
- Utilisateur: `$CLAUDE_DB_USER`
- Base: `$CLAUDE_DB_NAME`
