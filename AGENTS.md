# Agent Instructions for Axon

Product monorepo for Synapse MLOps platform. Contains ML services, production services, and UI.
Deployed to fleet clusters via Argo CD (infrastructure managed by Cortex).

## Local Development

Local cluster: `kind-axon`

```bash
kubectl config use-context kind-axon
```

### Cluster Services

| Service | Namespace | Endpoint (in-cluster) | Purpose |
|---------|-----------|----------------------|---------|
| SeaweedFS S3 | seaweedfs-system | `seaweedfs-s3.seaweedfs-system.svc:8333` | Object storage for images, artifacts |
| SeaweedFS Filer | seaweedfs-system | `seaweedfs-filer.seaweedfs-system.svc:8888` | File API for SeaweedFS |
| Argo Workflows | argo-workflows | `argo-workflows-argo-workflows-server.argo-workflows.svc:2746` | Pipeline orchestration |
| Feast | feast-system | `feast-system-feast-feature-server.feast-system.svc:6566` | Feature store |
| KServe | kserve | - | Model serving |
| Valkey | valkey-system | `valkey-master.valkey-system.svc:6379` | Redis-compatible cache |
| PostgreSQL | postgres-system | - | Database |

### Port Forwarding (for local access)

```bash
kubectl port-forward -n argo-workflows svc/argo-workflows-argo-workflows-server 2746:2746
kubectl port-forward -n seaweedfs-system svc/seaweedfs-s3 8333:8333
kubectl port-forward -n feast-system svc/feast-system-feast-feature-server 6566:6566
```

## Stack

- **Runtime**: Bun
- **Language**: TypeScript with Effect-TS
- **UI**: Svelte 5
- **ML Pipelines**: Python with uv
- **Orchestration**: Argo Workflows
- **Feature Store**: Feast
- **Object Storage**: SeaweedFS (S3-compatible)
- **Model Serving**: KServe
- **Build**: Turborepo

## Structure

```
axon/
├── apps/                   # Deployable services and UI
│   └── <app>/
│       ├── src/
│       ├── deploy/
│       │   ├── base/       # Base Kubernetes manifests
│       │   └── overlays/   # Environment-specific patches
│       └── package.json
│
├── packages/               # Shared TypeScript libraries
│   └── <package>/
│       ├── src/
│       └── package.json
│
├── pipelines/              # ML pipelines (Python)
│   └── <pipeline>/
│       ├── src/
│       └── pyproject.toml
│
├── turbo.json
├── package.json
└── flake.nix
```

## Commands

```bash
nix develop                 # Enter dev shell

bun install                 # Install dependencies
bun run dev                 # Start all dev servers
bun run build               # Build all packages
bun run test                # Run all tests
bun run lint                # Lint all packages
```

## TypeScript Style

tsconfig.json - Effect-TS recommended:
```json
{
  "compilerOptions": {
    "strict": true,
    "exactOptionalPropertyTypes": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "moduleResolution": "bundler",
    "module": "ESNext",
    "target": "ESNext",
    "lib": ["ESNext", "DOM", "DOM.Iterable"],
    "isolatedModules": true,
    "skipLibCheck": true,
    "noEmit": true
  }
}
```

Formatting:
- 2-space indentation
- Semicolons required
- Named imports only (no default exports)
- Explicit return types on exported functions

Effect-TS patterns:
```typescript
import { Effect, pipe } from "effect";

export const fetchUser = (id: string): Effect.Effect<User, HttpError> =>
  pipe(
    Effect.tryPromise(() => fetch(`/api/users/${id}`)),
    Effect.flatMap((res) => Effect.tryPromise(() => res.json())),
    Effect.mapError((e) => new HttpError(e))
  );
```

Prefer generator syntax for complex flows:
```typescript
import { Effect } from "effect";

export const processOrder = (orderId: string): Effect.Effect<Order, OrderError> =>
  Effect.gen(function* () {
    const order = yield* getOrder(orderId);
    const validated = yield* validateOrder(order);
    const processed = yield* chargePayment(validated);
    return processed;
  });
```

## Svelte Style

Svelte 5 with TypeScript:
```svelte
<script lang="ts">
  import type { User } from "$lib/types";

  let { user, onSave }: { user: User; onSave: (u: User) => void } = $props();

  let name = $state(user.name);

  const handleSubmit = () => {
    onSave({ ...user, name });
  };
</script>

<form onsubmit={handleSubmit}>
  <input bind:value={name} />
  <button type="submit">Save</button>
</form>
```

Runes over legacy reactive syntax:
- `$state()` over `let x = value`
- `$derived()` over `$: x = ...`
- `$effect()` over `$: { ... }`
- `$props()` over `export let`

## Python Style

Package manager: uv
Linter/formatter: ruff

```bash
uv sync                     # Install dependencies
uv run pytest               # Run tests
uv run ruff check .         # Lint
uv run ruff format .        # Format
```

pyproject.toml:
```toml
[project]
name = "pipeline-name"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

## ML Pipelines

Pipelines live in `pipelines/<name>/` with structure:

```
pipelines/<name>/
├── pyproject.toml          # uv project config
├── uv.lock                  # Locked dependencies
├── feature_store.yaml      # Feast configuration (if using features)
├── workflow.yaml           # Argo Workflow definition
├── features/               # Feast feature definitions
│   ├── __init__.py
│   ├── entities.py
│   └── views.py
├── src/
│   └── <name>/
│       ├── __init__.py
│       └── steps/          # Individual workflow steps
│           ├── __init__.py
│           ├── prepare.py
│           ├── train.py
│           └── evaluate.py
└── tests/
```

### Argo Workflows

Workflows are defined as Kubernetes manifests:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: pipeline-name-
  namespace: dev
spec:
  entrypoint: main
  serviceAccountName: argo-workflow
  artifactRepositoryRef:
    configMap: artifact-repositories
    key: default-v1
  templates:
    - name: main
      steps:
        - - name: step-one
            template: step-one-template
        - - name: step-two
            template: step-two-template
```

### Feast Integration

Connect to cluster Feast from pipelines:

```python
from feast import FeatureStore

store = FeatureStore(repo_path=".")
```

feature_store.yaml for local development:
```yaml
project: my_pipeline
registry: data/registry.db
provider: local
online_store:
  type: sqlite
  path: data/online_store.db
```

feature_store.yaml for cluster:
```yaml
project: my_pipeline
registry:
  registry_type: sql
  path: postgresql://user:pass@postgres.postgres-system.svc:5432/feast
provider: local
online_store:
  type: redis
  connection_string: valkey-master.valkey-system.svc:6379
```

### SeaweedFS Access

From Python (using boto3 with S3 API):
```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://seaweedfs-s3.seaweedfs-system.svc:8333",
    aws_access_key_id="any",
    aws_secret_access_key="any",
)
s3.upload_file("local.parquet", "bucket-name", "path/to/file.parquet")
```

## Kubernetes Manifests

Apps include deployment manifests in `deploy/`:

```
apps/<app>/deploy/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── namespace.yaml
    └── production/
        ├── kustomization.yaml
        └── namespace.yaml
```

YAML style:
- Multi-document files use `---` separator
- Field order: apiVersion, kind, metadata, spec
- Always specify namespace
- No comments
- Explicit image tags (never `latest`)

## Nix Style

Group packages by purpose:
```nix
buildInputs = with pkgs; [
  bun
  turbo

  uv
  python312

  kubectl
  kustomize

  just
  jq
];
```

## Commits

Conventional commits. Format: `type: description`

Types:
- `feat`: new feature or capability
- `fix`: bug fix
- `docs`: documentation only
- `refactor`: code change that neither fixes nor adds
- `chore`: maintenance, dependencies, tooling
- `ci`: CI/CD changes
- `test`: adding or updating tests

Examples:
- `feat: add user authentication service`
- `fix: correct order validation logic`
- `chore: update effect to v3.12`
- `refactor: simplify pipeline error handling`

Rules:
- Lowercase type and description
- No period at end
- Imperative mood
- Max 72 characters

## Testing

```bash
bun test                    # Run all tests
bun test --watch            # Watch mode
bun test apps/example       # Test specific package
```

For Python pipelines:
```bash
cd pipelines/<name>
uv run pytest
```

## Do Not

- Use default exports in TypeScript
- Use `as any` or `@ts-ignore`
- Use legacy Svelte reactive syntax (`$:`, `export let`)
- Use `latest` image tags
- Add comments to YAML or Kubernetes manifests
- Commit secrets or .env files
- Use emojis in code or logs
