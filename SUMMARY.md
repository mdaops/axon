# Discount Decisioning System - Learning Project

MLOps learning project: Build a real-time discount decisioning system to learn
the full ML lifecycle while exercising the Synapse platform infrastructure.

## Quick Links

- **PLAN.md** - Strategy, architecture, decisions
- **PHASES.md** - Detailed step-by-step guide (start here for implementation)

## Current Status

| | |
|-|-|
| **Phase** | 1 Complete ✅ → Phase 2 next |
| **Last Updated** | 2026-01-16 |

## Use Case

E-commerce discount decisioning: Given a user's browsing session, decide whether
to offer a discount coupon to increase conversion probability.

## Architecture Target

```
Events → Kafka → Flink → Feast → Model → Decision
         (Strimzi) (streaming)  (features) (KServe)
```

## Phase Summary

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Vertical Slice (data → model → serve) | ✅ Complete |
| 2 | Orchestrated Training (Argo Workflows) | ⏳ Next |
| 3 | Feature Store (Feast) | ⏳ Pending |
| 4 | Online Features | ⏳ Pending |
| 5 | Streaming (Kafka + Flink) | ⏳ Pending |
| 6 | Experimentation (A/B) | ⏳ Pending |

## Phase 1 Recap

```
Local: generate data → train model → model.joblib
                                          ↓
                                    S3 (SeaweedFS)
                                          ↓
                              KServe InferenceService
                                          ↓
                                   HTTP endpoint
```

**Endpoint working**: `curl → {"predictions": [0, 1]}`

## Infrastructure (axon cluster)

| Component | Namespace | Status |
|-----------|-----------|--------|
| SeaweedFS | seaweedfs-system | ✅ Ready |
| KServe | kserve | ✅ Ready |
| Istio | istio-system | ✅ Ready |
| Argo Workflows | argo-workflows | ✅ Ready |
| Feast | feast-system | ✅ Ready |
| Valkey | valkey-system | ✅ Ready |
| CloudNativePG | postgres-system | ✅ Ready |
| Strimzi | kafka-system | ✅ Ready |
| Flink | flink-system | ✅ Ready |

## Commands Quick Reference

```bash
cd axon/pipelines/discount-decisioning

# Generate data & train
uv run python data/generator.py
uv run python training/train.py

# Upload to S3
kubectl --context kind-axon port-forward -n seaweedfs-system svc/seaweedfs-s3 8333:8333 &
AWS_ACCESS_KEY_ID=any AWS_SECRET_ACCESS_KEY=any \
  aws s3 cp model/model.joblib s3://models/discount-decisioning/v1/model.joblib \
  --endpoint-url http://localhost:8333

# Deploy
kubectl --context kind-axon apply -f deploy/

# Test
kubectl --context kind-axon port-forward -n dev svc/discount-model-predictor 8080:80 &
curl -X POST http://localhost:8080/v1/models/discount-model:predict \
    -H "Content-Type: application/json" \
    -d '{"instances": [[300, 5, 49.99, 2]]}'
```

## Learnings Captured

### Phase 1
- KServe has two modes: Serverless (Knative) and RawDeployment (plain K8s)
- Use `serving.kserve.io/deploymentMode: RawDeployment` annotation without Knative
- ServiceAccount needs S3 secret attached for KServe to pull models
- `model.joblib` is sklearn's expected format for KServe runtime
- SeaweedFS doesn't enforce auth in dev - any creds work
