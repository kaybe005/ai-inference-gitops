# GitOps-Driven AI Inference Microservice Platform

A portfolio platform connecting a local k3s cluster on Proxmox VE to AWS ECR and Terraform-managed cloud foundations.

## Repository tree

```text
.
├── app/                         # FastAPI proxy, backend adapters, tests, image
├── charts/ai-proxy/             # Helm deployment contract for ArgoCD
├── terraform/
│   ├── bootstrap/               # One-time local-state creation of S3/DynamoDB
│   ├── platform/                # Remote-state-backed platform root
│   └── modules/ecr/             # Immutable ECR repository module
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/build-push.yml
└── README.md
```

## Five-phase execution sequence

1. **Application baseline:** implement and test the FastAPI proxy with mock backend; build locally for both architectures.
2. **AWS foundation:** apply `terraform/bootstrap` once, configure the platform backend, then apply ECR and OIDC IAM with least privilege.
3. **CI image supply chain:** configure the GitHub OIDC role ARN secret, push a commit, and verify the immutable SHA manifest and ECR scan.
4. **Local GitOps delivery:** install ArgoCD on k3s, point it at this public repository, configure Helm values with the ECR image, and verify rolling sync/probes.
5. **Operations:** install kube-prometheus-stack, enable the chart ServiceMonitor, add Grafana dashboards/alerts, and document recovery drills.

## Debugging checklist

- **ECR pulls:** private ECR credentials expire after 12 hours. Create a least-privilege pull secret or automate refresh; verify the secret namespace and image registry hostname. For a public portfolio repository, keep the chart secret-free and document the cluster-specific secret overlay.
- **Apple Silicon:** CI uses Buildx and QEMU to publish `linux/amd64` and `linux/arm64`. Verify the manifest with `docker buildx imagetools inspect`; avoid architecture-specific wheels or binaries.
- **ArgoCD loops:** use immutable SHA tags/digests, keep generated resources out of Git, avoid mutating Helm output in-cluster, and use `ignoreDifferences` only for a known controller-owned field.
- **Terraform locking:** bootstrap before initializing the platform backend. Never run concurrent applies. For a lock error, inspect the lock owner and running processes before using `force-unlock`.
- **Ollama reachability:** `localhost` in a pod is the pod, not the Proxmox host. Use a routable service/DNS address and NetworkPolicy/firewall rules; keep mock mode as the deterministic fallback.
- **OIDC failures:** confirm the GitHub `sub` condition matches the repository/branch and that the workflow has `id-token: write`; do not replace OIDC with static keys.
