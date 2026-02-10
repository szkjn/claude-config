#!/bin/bash
# Read-only PostgreSQL query wrapper for Claude
# Usage: ./scripts/db-query.sh "SELECT ..."
#        ./scripts/db-query.sh  (interactive mode)

set -e

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: .env file not found at $ENV_FILE" >&2
  exit 1
fi

CLAUDE_DB_HOST=$(grep ^CLAUDE_DB_HOST "$ENV_FILE" | cut -d= -f2)
CLAUDE_DB_PORT=$(grep ^CLAUDE_DB_PORT "$ENV_FILE" | cut -d= -f2)
CLAUDE_DB_NAME=$(grep ^CLAUDE_DB_NAME "$ENV_FILE" | cut -d= -f2)
CLAUDE_DB_USER=$(grep ^CLAUDE_DB_USER "$ENV_FILE" | cut -d= -f2)
CLAUDE_DB_PASSWORD=$(grep ^CLAUDE_DB_PASSWORD "$ENV_FILE" | cut -d= -f2)

if [ -z "$CLAUDE_DB_HOST" ] || [ -z "$CLAUDE_DB_NAME" ] || [ -z "$CLAUDE_DB_USER" ] || [ -z "$CLAUDE_DB_PASSWORD" ]; then
  echo "Error: missing one or more CLAUDE_DB_* variables in .env" >&2
  exit 1
fi

export PGPASSWORD="$CLAUDE_DB_PASSWORD"

PSQL_OPTS="-h $CLAUDE_DB_HOST -p ${CLAUDE_DB_PORT:-5432} -U $CLAUDE_DB_USER -d $CLAUDE_DB_NAME --no-password"

if [ -n "$1" ]; then
  psql $PSQL_OPTS -c "$1"
else
  psql $PSQL_OPTS
fi
