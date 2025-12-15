# LangGraph Neo4j Agents

A graph-RAG reference implementation that wires five LangGraph agents (query analyzer, entity resolver, data loader, traversal scout, and omnichannel responder) to Neo4j and exposes them through a FastAPI backend plus a Next.js chatbot UI. The system targets

- **Local prototyping on Apple Silicon** via Docker Compose, and
- **x86 OpenShift clusters** via an automated manifest generation workflow.

## Repository layout

```
backend/   FastAPI + LangGraph app, Neo4j tooling, Dockerfile
frontend/  Next.js App Router UI, Dockerfile
deployment/ scripts and OpenShift/Kubernetes templates
```

## Architecture highlights

- **Agents**: Query analyzer (with Wikipedia intent hints) → entity resolver → branch to data loader (ingestion) or traversal agent (retrieval) → omnichannel responder.
- **Tools**: Neo4j driver for writes/reads, Red Hat Llama 3.1 (HTTP) as the shared reasoning model.
- **APIs**: `POST /api/ingest` for loading new text, `POST /api/chat` for retrieval, `GET /health` for probes.

## Local development on macOS ARM

1. **Prerequisites**
   - Docker Desktop (or Colima) with Buildx enabled.
   - Python 3.11+, Node.js 20+ (only necessary if you prefer running without containers).

2. **Environment variables**
   - Copy `backend/.env.example` to `backend/.env` when running locally outside Docker.
   - For Docker Compose, create a root `.env` (already gitignored) if you want to override the defaults from `docker-compose.yml`; otherwise, the Truist endpoints are used automatically.
   - When pointing at the managed Neo4j instance, use the Bolt endpoint (`bolt://neo4j.neo4j.svc.cluster.local:7687` if using the provided manifest, or `bolt+s://...` if TLS is available). The `neo4j+s://` routing scheme requires a clustered database and will fail with `Unable to retrieve routing information` on single-node deployments.

3. **Docker Compose workflow**

   ```bash
   # Optional: override platform if you are *not* on Apple Silicon
   echo "LOCAL_DOCKER_PLATFORM=linux/arm64/v8" > .env

   docker compose up --build
   # backend: http://localhost:8000  frontend: http://localhost:3000
   ```

   The compose file pins `platform` to `linux/arm64/v8` so images run natively on Apple Silicon. Override `LOCAL_DOCKER_PLATFORM` if you need a different architecture.

4. **Direct execution (no containers)**

   ```bash
   # Backend
   cd backend && python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000

   # Frontend
  cd ../frontend
  npm install
  cat <<'EOF' > .env.local
  BACKEND_API_BASE_URL=http://localhost:8000
  NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
  EOF
  npm run dev
   ```

## Building linux/amd64 images for OpenShift

Use the helper script to cross-compile x86 images from your ARM laptop. Provide a registry you can push to (Quay, Docker Hub, etc.).

```bash
export REGISTRY=quay.io/your-org
export IMAGE_TAG=openshift
# optional: override the baked-in frontend public API base
# export FRONTEND_PUBLIC_API_BASE_URL=http://langgraph-backend:8000
# Optional: disable pushing by setting PUSH=false (defaults true)
docker login
./deployment/scripts/build-images.sh
```

Variables:
- `REGISTRY` – required.
- `BACKEND_IMAGE_NAME`, `FRONTEND_IMAGE_NAME` – defaults `langgraph-backend` / `langgraph-frontend`.
- `IMAGE_TAG` – defaults `latest`.
- `PLATFORM` – defaults `linux/amd64`.
- `FRONTEND_PUBLIC_API_BASE_URL` – baked into the frontend bundle; defaults `http://langgraph-backend:8000`.
- `PUSH` – `true` pushes via Buildx, `false` loads into the local daemon.

## Build & push linux/amd64 images

OpenShift is x86_64-only, so always publish `linux/amd64` images before deploying. The helper script takes care of building (via Buildx) and pushing both backend/frontend.

```bash
export REGISTRY=bhajian                  # or quay.io/<org>
export IMAGE_TAG=latest                 # pick a semver/tag you like
# optional overrides:
# export PLATFORM=linux/amd64
# export PUSH=false   # set to 'true' (default) to push instead of loading locally

./deployment/scripts/build-images.sh
```

Outputs:

```
Backend:  $REGISTRY/langgraph-backend:$IMAGE_TAG
Frontend: $REGISTRY/langgraph-frontend:$IMAGE_TAG
```

Once the script finishes (and `docker login` is configured for your registry), the images are ready for the deploy step below. The script uses `backend/Dockerfile.amd64` and `frontend/Dockerfile.amd64`, which pin the base images to linux/amd64 so you can cross-build on an Apple Silicon Mac without additional flags.

## Automated OpenShift deployment

1. **Log in** with the provided credentials:
   ```bash
   oc login https://api.truist-test.sandbox403.opentlc.com:6443 -u kubeadmin -p AEb6v-pRAE4-CMuFT-nxZec
   ```

2. **Set the required environment** and run the deploy script. It renders Kubernetes/OpenShift manifests from templates, then applies them via `oc apply`.

   ```bash
   export NAMESPACE=langgraph-rag
   export BACKEND_IMAGE=quay.io/your-org/langgraph-backend:openshift
   export FRONTEND_IMAGE=quay.io/your-org/langgraph-frontend:openshift
   export NEO4J_PASSWORD=Neo4jStrongPassword123
   # optional overrides
   export BACKEND_API_BASE_URL=http://langgraph-backend:8000
   export NEXT_PUBLIC_API_BASE_URL=$BACKEND_API_BASE_URL

   ./deployment/scripts/deploy-openshift.sh
   ```

   The script writes rendered YAML to `deployment/k8s/generated/` (gitignored) before applying them. Resources include:
   - Namespace, ConfigMap, and Secret for configuration data
   - Backend/Frontend Deployments, Services, and OpenShift Routes

3. **Monitor**
   ```bash
   oc get pods -n "$NAMESPACE"
   oc get routes -n "$NAMESPACE"
   ```

### Neo4j (non-TLS) redeploy

A self-contained Neo4j manifest set is available under `deployment/k8s/neo4j/`. It provisions a namespace, PVC, single-replica Deployment, and ClusterIP Service that exposes Bolt (7687) and HTTP (7474) without TLS. Apply it separately before deploying the LangGraph stack if you need an in-cluster database:

```bash
oc apply -f deployment/k8s/neo4j/namespace.yaml
oc apply -f deployment/k8s/neo4j/pvc.yaml
oc apply -f deployment/k8s/neo4j/deployment.yaml
oc apply -f deployment/k8s/neo4j/service.yaml
oc apply -f deployment/k8s/neo4j/route.yaml
```

The `neo4j` service is of type `LoadBalancer`, so OpenShift will allocate an external hostname/IP for Bolt (7687) and the HTTP console (7474). Retrieve it with:

```bash
oc get svc neo4j -n neo4j -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Point the backend (locally or in OpenShift) to this host via `NEO4J_URI=bolt://<external-host>:7687` (note the plain Bolt scheme). For local Docker Compose runs we default to the current load balancer hostname (`aadd3663d6966433cb14c2949e347874-822615571.us-east-1.elb.amazonaws.com`)—update it in `.env`/`docker-compose.yml` whenever the service assigns a new one.

> The included `neo4j-http` Route exposes the Neo4j Browser (port 7474) so you can test from your laptop. OpenShift Routes only proxy HTTP(S); Bolt traffic comes through the load balancer hostname retrieved above.
## Deployment assets

- `deployment/k8s/templates/*.yaml` – envsubst-friendly templates for namespace, config, secrets, deployments, services, and routes.
- `deployment/scripts/build-images.sh` – Buildx helper for producing linux/amd64 images.
- `deployment/scripts/deploy-openshift.sh` – Renders + applies manifests to the target cluster.

## API quick reference

| Endpoint | Description |
| --- | --- |
| `POST /api/ingest` | Runs the ingest branch of the LangGraph workflow and persists entities/relationships into Neo4j. |
| `POST /api/chat` | Executes the retrieval branch (query analyzer → traversal → omnichannel reply). |
| `GET /health` | Basic readiness/liveness probe. |

Both API routes expect/return JSON in the shapes defined under `backend/app/schemas.py`.

## Notes

- `.env` files are ignored globally per `.gitignore`; store local secrets there.
- Wikipedia calls inside the query analyzer require outbound network access.
- TLS verification against the provided Llama endpoint is disabled in code (`verify=False`) because of the provided certificate; adjust when mounting trusted certs in production.
# graph-rag
