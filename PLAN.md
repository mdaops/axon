# Discount Decisioning - Learning Plan

## Goal

Learn MLOps by building a discount decisioning system end-to-end, using the
Synapse platform infrastructure (deployed via cortex to axon cluster).

This is a **learning project** - the point is understanding, not delivery.

## How to Use This Repo

1. **SUMMARY.md** - Quick reference, current status
2. **PLAN.md** (this file) - Overall strategy, architecture decisions
3. **PHASES.md** - Detailed step-by-step guide with concepts explained

## Session Continuity

These docs should be comprehensive enough for any agent session to:
1. Understand where we are
2. Know what's been done
3. Continue from the current point
4. Maintain the learning-oriented approach

Update docs as we go. Capture learnings, gotchas, decisions.

---

## Phases Overview

| Phase | Focus | ML Complexity | Platform Complexity |
|-------|-------|---------------|---------------------|
| 1 | Vertical Slice | Logistic regression | KServe + SeaweedFS |
| 2 | Orchestration | Same model | Argo Workflows |
| 3 | Feature Store | Feature engineering | Feast + Postgres + Valkey |
| 4 | Online Features | Custom serving | Feast online serving |
| 5 | Streaming | Real-time features | Kafka + Flink |
| 6 | Experimentation | A/B testing | Traffic splitting + monitoring |

---

## Architecture

### Current State (Phase 1 Target)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         axon cluster (kind-axon)                     │
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │   Training   │────▶│  SeaweedFS   │◀────│   KServe     │         │
│  │   (local)    │     │   (S3)       │     │   sklearn    │         │
│  └──────────────┘     └──────────────┘     └──────────────┘         │
│        │                    │                     │                  │
│        │                    │                     │                  │
│   model.joblib         s3://models/         InferenceService        │
│                      discount-decisioning/                           │
│                           v1/                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### End State (Phase 6 Target)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         axon cluster (kind-axon)                     │
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  Kafka   │───▶│  Flink   │───▶│  Feast   │───▶│  KServe  │      │
│  │ (events) │    │ (stream) │    │ (online) │    │  (serve) │      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│       ▲                               │                ▲            │
│       │                               │                │            │
│  ┌────┴─────┐                   ┌─────▼────┐    ┌─────┴─────┐      │
│  │ Simulator│                   │  Feast   │    │   Argo    │      │
│  │ (events) │                   │ (offline)│◀───│ Workflows │      │
│  └──────────┘                   └──────────┘    └───────────┘      │
│                                      │                              │
│                                ┌─────▼─────┐                       │
│                                │ SeaweedFS │                       │
│                                │   (S3)    │                       │
│                                └───────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Entity: User Session

A browsing session on the e-commerce site. Core entity for features.

```python
session = {
    "session_id": "uuid",
    "user_id": "uuid",           # nullable for anonymous
    "timestamp": "datetime",
    "events": [...]              # page views, cart actions, etc.
}
```

### Target Variable

`converted`: Did the user complete a purchase in this session?

### Features (evolving by phase)

**Phase 1** (raw features, no feature store):
- session_duration_seconds
- pages_viewed  
- cart_value
- items_in_cart

**Phase 3+** (computed features via Feast):
- user_sessions_last_7d
- user_total_spend_last_30d
- user_cart_abandonment_rate
- category_affinity_scores
- time_since_last_purchase

---

## Model Evolution

| Phase | Model | Why |
|-------|-------|-----|
| 1 | sklearn LogisticRegression | Simplest, interpretable, KServe has native runtime |
| 2 | Same | Focus is on orchestration, not model improvement |
| 3 | sklearn GradientBoosting | Better with engineered features |
| 4 | Same | Focus is on serving architecture |
| 5 | Same | Focus is on streaming infrastructure |
| 6 | Experiment with alternatives | Compare models via A/B |

---

## Infrastructure (Deployed via Cortex)

All infrastructure lives on axon cluster, deployed by Flux from cortex.

### Phase 1 Requirements

| Component | Namespace | Status | Purpose |
|-----------|-----------|--------|---------|
| SeaweedFS | seaweedfs-system | ✅ Ready | Model storage (S3) |
| Istio | istio-system | ✅ Ready | KServe dependency |
| KServe | kserve | ✅ Ready | Model serving |
| cert-manager | cert-manager | ✅ Ready | TLS certificates |

### Future Phase Requirements

| Component | Namespace | Status | Phase |
|-----------|-----------|--------|-------|
| Argo Workflows | argo-workflows | ✅ Ready | 2 |
| CloudNativePG | postgres-system | ✅ Ready | 3 |
| Valkey | valkey-system | ✅ Ready | 3, 4 |
| Feast | feast-system | ✅ Ready | 3, 4 |
| Strimzi (Kafka) | kafka-system | ✅ Ready | 5 |
| Flink | flink-system | ✅ Ready | 5 |

---

## Directory Structure (Actual)

```
axon/
├── SUMMARY.md              # Quick reference
├── PLAN.md                 # This file - strategy
├── PHASES.md               # Detailed walkthrough
├── AGENTS.md               # Agent instructions
│
└── pipelines/
    └── discount-decisioning/
        ├── pyproject.toml
        ├── uv.lock
        ├── .gitignore
        │
        ├── data/                   # Data generation module
        │   ├── __init__.py
        │   └── generator.py        # ✅ Created
        │
        ├── training/               # Training module
        │   ├── __init__.py
        │   └── train.py            # ✅ Created
        │
        ├── model/                  # Local model output (gitignored)
        │   └── model.joblib        # ✅ Trained
        │
        ├── data/                   # Local data (gitignored) - note: shadows module
        │   └── sessions.parquet    # ✅ Generated
        │
        ├── deploy/                 # K8s manifests (Phase 1.6)
        │   ├── s3-secret.yaml
        │   └── inference-service.yaml
        │
        ├── features/               # Feast definitions (Phase 3+)
        ├── workflows/              # Argo Workflows (Phase 2+)
        └── tests/
```

---

## Current Status

**Phase**: 1 - Vertical Slice  
**Step**: 1.5 - Upload Model to S3

### Completed
- [x] Infrastructure verified on axon cluster
- [x] S3 bucket created (`s3://models`)
- [x] Learning docs created (SUMMARY, PLAN, PHASES)
- [x] Pipeline skeleton created (pyproject.toml, directories)
- [x] Data generator written and run (10k sessions, ~30% conversion)
- [x] Training script written and run (~75% accuracy)
- [x] Model saved locally (`model/model.joblib`)

### In Progress
- [ ] Upload model to SeaweedFS S3

### Up Next
- [ ] Create K8s manifests (Secret, InferenceService)
- [ ] Deploy InferenceService
- [ ] Test endpoint

---

## Learning Outcomes

By the end of this project, should understand:

- [x] How ML models are trained and serialized (Phase 1 - in progress)
- [ ] How feature stores work (offline vs online)
- [ ] How model serving works (KServe, inference protocols)
- [ ] How ML pipelines are orchestrated (Argo Workflows)
- [ ] How streaming features work (Kafka → Flink → Feast)
- [ ] How experiments are run (A/B, canary deployments)
- [ ] How all of this maps to Kubernetes infrastructure

---

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-16 | Use discount decisioning use case | Exercises full stack, clear business logic, easy to simulate |
| 2026-01-16 | Start with synthetic data | Control complexity, debug easily, add realism later |
| 2026-01-16 | sklearn first, not PyTorch | KServe has native runtime, simpler serialization |
| 2026-01-16 | Flat package structure | Simpler than src/ layout for learning project |
| 2026-01-16 | Direct script execution | `uv run python data/generator.py` vs module imports |

---

## Glossary

Terms we'll encounter:

- **Feature Store**: Centralized store for ML features, ensures consistency between training and serving
- **Offline Store**: Historical feature storage (Postgres, BigQuery) for training
- **Online Store**: Low-latency feature storage (Redis/Valkey) for inference
- **Point-in-time correctness**: Ensuring training uses only features available at prediction time (no data leakage)
- **InferenceService**: KServe CRD that defines a deployed model
- **Predictor**: The model serving component within an InferenceService
- **Materialization**: Computing and storing feature values from raw data
