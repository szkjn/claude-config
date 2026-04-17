# Wisepipe Database Schema

Base de donnees PostgreSQL de production pour le projet Wisepipe.

## Tables

### batches
Gestion des lots d'import de sources.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK, auto-increment |
| filename | text | Nom du fichier source |
| source | text | Source du batch |
| status | text | Statut du traitement |
| url | text | URL source |
| timestamp | bigint | Timestamp Unix |
| created_at | timestamp | Date de creation |
| updated_at | timestamp | Date de mise a jour |
| nb_trials | integer | Nombre de tentatives (default: 0) |

**Relations:** Reference par `documents.batch_id`

---

### documents
Table principale des documents indexes.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK, auto-increment |
| batch_id | integer | FK vers batches |
| identifier | text | Identifiant du document |
| official_id | text | ID officiel |
| wisetax_id | text | ID Wisetax unique |
| timestamp | text | Timestamp |
| identifier_perm | text | Identifiant permanent (UNIQUE) |
| url | text | URL du document |
| status | text | Statut |
| s3_key | text | Cle S3 du document |
| version | integer | Version (default: 0) |
| type | text | Type de document |
| format | text | Format (pdf, html, etc.) |
| hash | text | Hash du contenu |
| error | jsonb | Erreurs eventuelles |
| nb_trials | integer | Nombre de tentatives |

**Flags de traitement:**
- links, plan, version_set, score, images, expertise, onthology, main_links
- chunk_selection, chunk, fiche, jp_relative, chunk_indexed, ape_idcc_mapped
- q_expertises, domain_social_set

Chaque flag a un compteur `*_trials` associe.

**Relations:**
- FK vers `batches(id)`
- Reference par `chunks.document_id`, `links.document_id`

---

### chunks
Fragments de documents pour l'indexation et l'embedding.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK, auto-increment |
| document_id | integer | FK vers documents |
| indexable_text | text | Texte indexable |
| wisetax_id | text | ID Wisetax |
| chunk | integer | Numero du chunk |
| chunk_id | text | ID unique du chunk (UNIQUE) |
| link | text | Lien |
| breadcrumbs | text | Fil d'ariane |
| content | text | Contenu du chunk |
| num | text | Numero |
| embedding | vector(768) | Embedding v1 |
| embedding_v3 | vector(1024) | Embedding v3 |

**Flags:** embedded, pinecone, pinecone_removed, embedded_v3, pinecone_v3, pinecone_v3_removed (avec *_trials)

---

### links
Relations entre documents.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK, auto-increment |
| identifier_perm | text | Identifiant permanent source |
| source | text | Source |
| type | text | Type de lien |
| target_identifier | text | Identifiant cible |
| direction | text | Direction du lien |
| external | boolean | Lien externe (default: false) |
| status | text | Statut |
| target_corpus | text | Corpus cible |
| name | text | Nom du lien |
| target_wisetax_id | text | ID Wisetax cible |
| target_text | text | Texte cible |
| document_id | integer | FK vers documents |
| error | text | Erreur |

---

### external_docs
Documents externes (PDFs uploades).

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK, auto-increment |
| s3_path | text | Chemin S3 |
| title | text | Titre |
| status | text | Statut |
| wisetax_id | text | ID Wisetax |
| description | text | Description |
| external_id | text | ID externe |
| date | timestamp | Date du document |
| date_fin | timestamp | Date de fin de validite |
| domain | jsonb | Domaines |
| expertise | jsonb | Expertises |
| country | jsonb | Pays |

**Flags:** chunk_indexed, is_described (avec *_trials)

---

### job_runs
Historique des executions de jobs.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK, auto-increment |
| name | text | Nom du job |
| status | text | Statut |
| error | text | Erreur |
| started_at | bigint | Timestamp debut |
| finished_at | bigint | Timestamp fin |
| nb_rows | integer | Nombre de lignes traitees |
| remainer | bigint | Lignes restantes |

---

### manual_refs
References manuelles entre documents.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK, auto-increment |
| source | text | Source |
| target | text | Cible |
| type | text | Type de reference |
| status | text | Statut |
| trials | integer | Tentatives |
| anchor | text | Ancre |

---

### config
Configuration globale.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK |
| global_switch | boolean | Switch global (default: false) |
| serverless_switch | boolean | Switch serverless (default: false) |

---

### summary_ratings
Evaluations des resumes generes.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | PK, auto-increment |
| wisetax_id | text | ID Wisetax |
| full_text | text | Texte complet |
| summary | text | Resume |
| prompt | text | Prompt utilise |
| rating | integer | Note |
| rating_comment | text | Commentaire |
| method | text | Methode utilisee |
