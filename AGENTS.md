# Agent Instructions for Axon

Product monorepo for Synapse MLOps platform. Contains ML services, production services, and UI.
Deployed to fleet clusters via Argo CD (infrastructure managed by Cortex).

## Stack

- **Runtime**: Bun
- **Language**: TypeScript with Effect-TS
- **UI**: Svelte 5
- **ML Pipelines**: Python with uv
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
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
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
