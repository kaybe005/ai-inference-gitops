# Repository instructions

## Mission
This repository implements a GitOps-driven AI inference microservice platform bridging a local k3s cluster on Proxmox VE with AWS automation.

## Environment
- Developer workstation: Apple Silicon M2 MacBook Air.
- Local cluster host: Dell OptiPlex 7080, Intel i7-10800, 16 GB RAM, 512 GB storage, Proxmox VE, k3s.
- AWS region: `ap-southeast-2`.
- AWS services in scope: ECR, S3, DynamoDB, IAM, CloudWatch where needed.

## Architectural invariants
- FastAPI is the application boundary; inference uses a backend interface supporting `mock` and `ollama`.
- CI publishes immutable Git-SHA image tags and linux/amd64 plus linux/arm64 manifests.
- GitHub Actions authenticates with AWS OIDC; never add long-lived AWS access keys.
- Terraform bootstrap creates the S3 state bucket and a legacy DynamoDB lock table. Platform Terraform uses the S3 backend's native lock file and requires Terraform >= 1.10.
- ECR repositories use immutable tags, encryption, scanning, and lifecycle cleanup.
- Helm is the deployment contract. ArgoCD syncs the public repository; the image publish workflow commits SHA tag updates and must not create a build loop.
- Kubernetes workloads must use probes, resource requests/limits, non-root security contexts, and rolling updates with zero unavailable replicas.
- Secrets must never be committed. Use Kubernetes Secrets, External Secrets, GitHub Secrets, or documented placeholders.

## Engineering rules
- Prefer small, typed, testable Python modules and explicit error handling.
- Preserve compatibility with Python 3.12, k3s, Helm 3, Terraform >= 1.10, and current GitHub Actions versions.
- Keep values configurable; do not hardcode AWS account IDs, repository URLs, credentials, or cluster-specific addresses.
- Validate payloads at the API boundary and expose `/healthz`, `/readyz`, and `/metrics`.
- Run focused unit tests, `terraform fmt -check`, `terraform validate`, `helm lint`, and YAML/action syntax checks when relevant.
- Do not push or apply infrastructure without explicit user instruction.

## Known operational constraints
- M2 Docker builds require Buildx/QEMU for amd64 output; local k3s on the Intel Dell node requires amd64 availability.
- Private ECR pulls from k3s require a refreshed `imagePullSecret` because ECR auth tokens expire; prefer a scoped pull role and an automated refresh mechanism.
- Ollama must be reachable from the pod network; do not assume `localhost` refers to the Proxmox host.
- ArgoCD tracks immutable image tags committed by the publish workflow; preserve the workflow's values-only path filter to prevent image update loops.
- Terraform state locking must be respected; never delete a DynamoDB lock during an active apply. Recover stale locks only after verifying no Terraform process is running.
