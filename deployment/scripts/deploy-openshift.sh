#!/usr/bin/env bash
set -euo pipefail

: "${NAMESPACE:=langgraph-rag}"
: "${BACKEND_IMAGE:?Set BACKEND_IMAGE (e.g., quay.io/org/langgraph-backend:tag)}"
: "${FRONTEND_IMAGE:?Set FRONTEND_IMAGE (e.g., quay.io/org/langgraph-frontend:tag)}"
: "${LLAMA_API_URL:=https://redhataillama-31-8b-instruct-model-service.apps.truist-test.sandbox403.opentlc.com/v1/chat/completions}"
: "${LLAMA_MODEL:=redhataillama-31-8b-instruct}"
: "${NEO4J_URI:=neo4j+s://neo4j-neo4j.apps.truist-test.sandbox403.opentlc.com:7687}"
: "${NEO4J_USER:=neo4j}"
: "${NEO4J_PASSWORD:?Set NEO4J_PASSWORD}"
: "${NEO4J_DATABASE:=neo4j}"
: "${BACKEND_API_BASE_URL:=http://langgraph-backend:8000}"
: "${NEXT_PUBLIC_API_BASE_URL:=${BACKEND_API_BASE_URL}}"

command -v oc >/dev/null 2>&1 || { echo "oc CLI is required"; exit 1; }

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="${SCRIPT_DIR}/../k8s/templates"
GENERATED_DIR="${SCRIPT_DIR}/../k8s/generated"
mkdir -p "${GENERATED_DIR}"

export NAMESPACE BACKEND_IMAGE FRONTEND_IMAGE LLAMA_API_URL LLAMA_MODEL NEO4J_URI NEO4J_USER NEO4J_PASSWORD NEO4J_DATABASE BACKEND_API_BASE_URL NEXT_PUBLIC_API_BASE_URL

generate_file() {
  local template="$1"
  local target="$2"
  envsubst < "${template}" > "${target}"
}

for tmpl in "${TEMPLATE_DIR}"/*.yaml; do
  filename="$(basename "${tmpl}")"
  generate_file "${tmpl}" "${GENERATED_DIR}/${filename}"
  echo "Rendered ${filename}"
done

echo "Applying manifests to namespace ${NAMESPACE}"
oc apply -f "${GENERATED_DIR}/namespace.yaml"
for manifest in "${GENERATED_DIR}"/*.yaml; do
  if [[ "$(basename "${manifest}")" == "namespace.yaml" ]]; then
    continue
  fi
  oc apply -f "${manifest}"
done

echo "Deployment kicked off. Use 'oc get pods -n ${NAMESPACE}' to monitor status."
