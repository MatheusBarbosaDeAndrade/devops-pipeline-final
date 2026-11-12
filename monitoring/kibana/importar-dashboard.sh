#!/usr/bin/env bash
# Importa data view, visualizações e dashboard no Kibana (dashboard como código)
set -euo pipefail
KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Aguardando o Kibana em $KIBANA_URL ..."
until curl -fs "$KIBANA_URL/api/status" | grep -q '"level":"available"'; do sleep 5; done

curl -fsS -X POST "$KIBANA_URL/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  --form file=@"$DIR/dashboard-tarefas.ndjson"
echo
echo "Dashboard: $KIBANA_URL/app/dashboards#/view/tarefas-dashboard"
