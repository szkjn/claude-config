#!/bin/bash
# Read-only Elasticsearch query wrapper for Claude
# Usage: ./scripts/es-query.sh <endpoint> [json-body]
#        ./scripts/es-query.sh "_cluster/health"
#        ./scripts/es-query.sh "wisepipe-all-3/_search" '{"query":{"term":{"corpus":"BOSS"}},"size":5}'

set -e

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE" >&2
    exit 1
fi

ELASTICSEARCH_API_KEY_READONLY=$(grep ^ELASTICSEARCH_API_KEY_READONLY "$ENV_FILE" | cut -d= -f2)
ES_HOST=$(grep ^ELASTICSEARCH_HOST "$ENV_FILE" | cut -d= -f2)
ES_HOST="${ES_HOST:-https://wisetax.es.eu-west-1.aws.found.io}"

if [ -z "$ELASTICSEARCH_API_KEY_READONLY" ]; then
    echo "Error: ELASTICSEARCH_API_KEY_READONLY not set in .env" >&2
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: $0 <endpoint> [json-body]"
    echo ""
    echo "Examples:"
    echo "  $0 '_cluster/health'"
    echo "  $0 'wisepipe-all-3/_count'"
    echo "  $0 'wisepipe-all-3/_search' '{\"query\":{\"term\":{\"corpus\":\"BOSS\"}},\"size\":5}'"
    exit 1
fi

ENDPOINT="$1"
JSON_BODY="$2"

if [ -n "$JSON_BODY" ]; then
    # POST request with JSON body
    curl -s -H "Authorization: ApiKey $ELASTICSEARCH_API_KEY_READONLY" \
         -H "Content-Type: application/json" \
         "$ES_HOST/$ENDPOINT" \
         -d "$JSON_BODY"
else
    # GET request
    curl -s -H "Authorization: ApiKey $ELASTICSEARCH_API_KEY_READONLY" \
         "$ES_HOST/$ENDPOINT"
fi
