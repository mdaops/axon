# Discount Decisioning - Detailed Phases

Learning-oriented guide. Each phase explains concepts, provides exact steps,
and captures learnings. Comprehensive enough for session continuity.

---

## Phase 1: Vertical Slice ✅

**Status**: Complete  
**Goal**: Prove the full path works with the simplest possible implementation.

```
Synthetic Data → Train Model → Store in S3 → Serve via KServe → Call Endpoint
```

### Why Start Here?

Before adding complexity (features stores, streaming, etc.), validate that:
1. We can train a model and serialize it
2. We can store artifacts in SeaweedFS (S3)
3. KServe can load and serve the model
4. We can call the inference endpoint

If any of these fail, we debug now - not after adding 5 more layers.

---

### Concepts: What is KServe?

KServe provides inference on Kubernetes. Key ideas:

- **InferenceService**: Custom resource that defines what model to serve
- **Predictor**: The model server (sklearn, pytorch, tensorflow, custom)
- **Runtime**: Pre-built container that knows how to load/serve a model format
- **Storage**: Where the model artifact lives (S3, GCS, PVC, etc.)

**Deployment Modes**:
- **Serverless** (default) - requires Knative, scales to zero
- **RawDeployment** - plain K8s Deployment, always-on pod(s)

We use RawDeployment (no Knative in our cluster).

---

### 1.1 Create Pipeline Skeleton ✅

Created `pipelines/discount-decisioning/` with:
- `pyproject.toml` - dependencies: scikit-learn, pandas, numpy, joblib, pyarrow, boto3
- `uv.lock` - locked dependencies via `uv sync`
- `.gitignore` - ignores data/, model/, .venv/
- `data/__init__.py`, `training/__init__.py` - package init files

**Run**: `uv sync`

---

### 1.2 Data Generator ✅

**File**: `data/generator.py`

Generates synthetic e-commerce session data:
- `session_duration_seconds` - exponential distribution, 60-1800s
- `pages_viewed` - Poisson distribution (count data), avg 8
- `cart_value` - exponential distribution, 0-500
- `items_in_cart` - Poisson distribution, avg 2
- `converted` - binary, probability based on weighted features + noise

**Run**: `uv run python data/generator.py`  
**Output**: `data/sessions.parquet` (~10k rows, ~30% conversion rate)

---

### 1.3 Training Script ✅

**File**: `training/train.py`

- Loads parquet data
- Splits 80/20 train/test
- Trains LogisticRegression (sklearn)
- Evaluates accuracy, precision, recall
- Saves model as `model/model.joblib`

**Run**: `uv run python training/train.py`  
**Output**: ~75% accuracy on test set

---

### 1.4 Upload Model to SeaweedFS ✅

```bash
kubectl --context kind-axon port-forward -n seaweedfs-system svc/seaweedfs-s3 8333:8333 &

AWS_ACCESS_KEY_ID=any AWS_SECRET_ACCESS_KEY=any \
  aws s3 cp model/model.joblib s3://models/discount-decisioning/v1/model.joblib \
  --endpoint-url http://localhost:8333
```

Model stored at `s3://models/discount-decisioning/v1/model.joblib`

---

### 1.5 Create K8s Manifests ✅

**`deploy/s3-secret.yaml`** - S3 credentials for KServe:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: s3-credentials
  namespace: dev
  annotations:
    serving.kserve.io/s3-endpoint: seaweedfs-s3.seaweedfs-system.svc:8333
    serving.kserve.io/s3-usehttps: "0"
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: any
  AWS_SECRET_ACCESS_KEY: any
```

**`deploy/inference-service.yaml`** - The InferenceService:
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: discount-model
  namespace: dev
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    sklearn:
      storageUri: s3://models/discount-decisioning/v1
      resources:
        requests:
          cpu: 100m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 512Mi
```

**Note**: `RawDeployment` annotation required - no Knative in cluster.

---

### 1.6 Deploy ✅

```bash
kubectl --context kind-axon apply -f deploy/s3-secret.yaml
kubectl --context kind-axon patch serviceaccount default -n dev \
    -p '{"secrets": [{"name": "s3-credentials"}]}'
kubectl --context kind-axon apply -f deploy/inference-service.yaml
```

**Why patch ServiceAccount?** KServe's init container runs as the namespace's default SA. 
Attaching the secret makes S3 creds available to download the model.

---

### 1.7 Test Endpoint ✅

```bash
kubectl --context kind-axon port-forward -n dev svc/discount-model-predictor 8080:80 &

curl -X POST http://localhost:8080/v1/models/discount-model:predict \
    -H "Content-Type: application/json" \
    -d '{"instances": [[300, 5, 49.99, 2], [1200, 25, 199.99, 5]]}'
```

**Response**: `{"predictions": [0, 1]}`

- `[300, 5, 49.99, 2]` → 0 (low engagement → no discount)
- `[1200, 25, 199.99, 5]` → 1 (high engagement → offer discount)

---

### Phase 1 Learnings

- Flat package structure (`data/`, `training/`) simpler than nested `src/` layout
- `uv sync` creates venv; `uv run <script>` executes with that venv
- Poisson distribution models count of events in fixed interval
- `model.joblib` is the format KServe sklearn runtime expects
- SeaweedFS accepts any credentials in dev (no auth enforcement)
- KServe defaults to Serverless mode (Knative) - use `RawDeployment` annotation without it
- ServiceAccount patching needed for KServe to access S3 credentials

---

## Phase 2: Orchestrated Training

**Status**: Not started  
**Goal**: Training runs as Argo Workflow, not local script.

### Production Flow (Target)

```
Code Push → Argo Workflow → Train → Push to S3 (v2) → Update Git → ArgoCD syncs
```

### Concepts to Cover
- Argo Workflows basics (templates, steps, DAGs)
- Container images for ML (Dockerfile)
- Artifact passing between steps
- Model versioning strategies
- GitOps model promotion

### Key Tasks
- [ ] Containerize training code (Dockerfile)
- [ ] Create Argo Workflow manifest
- [ ] Configure artifact repository (SeaweedFS)
- [ ] Run training as workflow
- [ ] Model versioned in S3
- [ ] (Stretch) Workflow updates Git manifest for GitOps

---

## Phase 3: Feature Store

**Status**: Not started  
**Goal**: Features defined in Feast, training uses feature SDK.

### Concepts to Cover
- Feature stores: why they exist
- Entities and feature views
- Point-in-time correctness (avoiding data leakage)
- Offline vs online stores

### Key Tasks
- [ ] Define Feast entities
- [ ] Create feature views
- [ ] Materialize features to offline store
- [ ] Training fetches from Feast

---

## Phase 4: Online Features

**Status**: Not started  
**Goal**: Inference fetches features in real-time from Feast.

### Concepts to Cover
- Online feature serving patterns
- Feature freshness requirements
- Custom inference services (transformer pattern)

### Key Tasks
- [ ] Materialize to online store (Valkey)
- [ ] Create custom predictor that fetches features
- [ ] End-to-end: session_id in → prediction out

---

## Phase 5: Streaming Features

**Status**: Not started  
**Goal**: Features update in real-time as events stream in.

### Concepts to Cover
- Stream processing fundamentals
- Kafka basics (topics, consumers, producers)
- Flink for stateful stream processing
- Lambda vs Kappa architecture

### Key Tasks
- [ ] Create Kafka topics for events
- [ ] Build Flink job for feature aggregation
- [ ] Push streaming features to Feast online store
- [ ] Event simulator for testing

---

## Phase 6: Experimentation

**Status**: Not started  
**Goal**: A/B test different models/strategies.

### Concepts to Cover
- Experiment design
- Traffic splitting (canary, percentage)
- Statistical significance
- Model monitoring and drift detection

### Key Tasks
- [ ] Deploy multiple model versions
- [ ] Configure traffic split in KServe
- [ ] Implement prediction logging
- [ ] Build monitoring dashboard
