#!/usr/bin/env bash
set -euo pipefail

: "${REGISTRY:?Set REGISTRY (e.g., quay.io/org)}"
: "${BACKEND_IMAGE_NAME:=langgraph-backend}"
: "${FRONTEND_IMAGE_NAME:=langgraph-frontend}"
: "${IMAGE_TAG:=latest}"
PLATFORM="${PLATFORM:-linux/amd64}"
PUSH="${PUSH:-true}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

build_cmd() {
  local component="$1"
  local context="$2"
  local image="$3"
  local dockerfile="$4"

  echo "\n==> Building ${image} for ${PLATFORM} using ${dockerfile}"
  if [[ "${PUSH}" == "true" ]]; then
    docker buildx build --platform "${PLATFORM}" -f "${dockerfile}" -t "${image}" "${context}" --push
  else
    docker buildx build --platform "${PLATFORM}" -f "${dockerfile}" -t "${image}" "${context}" --load
  fi
}

BACKEND_IMAGE="${REGISTRY}/${BACKEND_IMAGE_NAME}:${IMAGE_TAG}"
FRONTEND_IMAGE="${REGISTRY}/${FRONTEND_IMAGE_NAME}:${IMAGE_TAG}"

BACKEND_DOCKERFILE="${PROJECT_ROOT}/backend/Dockerfile.amd64"
FRONTEND_DOCKERFILE="${PROJECT_ROOT}/frontend/Dockerfile.amd64"

build_cmd "backend" "${PROJECT_ROOT}/backend" "${BACKEND_IMAGE}" "${BACKEND_DOCKERFILE}"
build_cmd "frontend" "${PROJECT_ROOT}/frontend" "${FRONTEND_IMAGE}" "${FRONTEND_DOCKERFILE}"

echo "\nImages built:"
echo "  Backend:  ${BACKEND_IMAGE}"
echo "  Frontend: ${FRONTEND_IMAGE}"
