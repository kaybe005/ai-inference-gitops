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
│   └── modules/
│       ├── ecr/                 # Immutable ECR repository module
│       └── github_oidc/         # GitHub Actions OIDC role
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/deploy.yml
└── README.md
```

## Five-phase execution sequence

1. **Application baseline:** run the FastAPI proxy with the mock backend. It exposes `/v1/models` and `/v1/chat/completions` for Open WebUI.
2. **AWS foundation:** apply `terraform/bootstrap` once, configure the platform backend, then apply ECR and the GitHub OIDC role. Supply the ARN of the existing GitHub Actions OIDC provider with `github_oidc_provider_arn`.
3. **CI image supply chain:** set the GitHub Actions secret `AWS_ROLE_ARN` to the Terraform output `github_actions_role_arn`. Allow the workflow's `GITHUB_TOKEN` to push to `main`. A push to `main` publishes an immutable SHA image and updates the chart repository and tag from the ECR login result.
4. **Local GitOps delivery:** install ArgoCD on k3s, point it at this public repository, and verify the Open WebUI and proxy apps sync with healthy probes.
5. **Operations:** install kube-prometheus-stack, enable the chart ServiceMonitor, add Grafana dashboards/alerts, and document recovery drills.

## GitHub Actions OIDC setup

The GitHub OIDC provider must already exist in the AWS account, with `sts.amazonaws.com` in its client ID list. After bootstrap and backend configuration, set its ARN for the platform Terraform root and create the role. The role trust uses this repository's immutable GitHub subject claim, including its owner and repository IDs:

```sh
export TF_VAR_github_oidc_provider_arn="arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com"
terraform -chdir=terraform/platform init
terraform -chdir=terraform/platform apply
terraform -chdir=terraform/platform output -raw github_actions_role_arn
```

Save the output as the repository Actions secret `AWS_ROLE_ARN`. If this repository is renamed, transferred, or its OIDC subject template changes, update `github_oidc_subject` to the exact claim GitHub issues. The workflow also needs permission to push its generated values-only commit to `main`.

## Debugging checklist

- **ECR pulls:** the `aws-ecr-secret` pull secret must be refreshed because ECR credentials expire after 12 hours. Verify the secret exists in the `default` namespace and matches the registry hostname.
- **Apple Silicon:** CI uses Buildx and QEMU to publish `linux/amd64` and `linux/arm64`. Verify the manifest with `docker buildx imagetools inspect`; avoid architecture-specific wheels or binaries.
- **Model discovery:** request `http://ai-proxy.default.svc.cluster.local:8080/v1/models` from inside the cluster. The result lists models installed in Ollama. `DEFAULT_MODELS` only preselects an available model; it does not install one. On the Ollama host, run `ollama list` and, if needed, `ollama pull llama3.2:3b`.
- **ArgoCD image updates:** the publish workflow commits the new immutable SHA tag to `charts/ai-proxy/values.yaml`. It ignores changes that only update that file, preventing a build loop.
- **Terraform locking:** the platform uses S3 native lock files and requires Terraform 1.10 or newer. Bootstrap before initializing the platform backend. Never run concurrent applies. For a lock error, inspect the lock owner and running processes before using `force-unlock`.
- **Ollama reachability:** `localhost` in a pod is the pod, not the Proxmox host. `charts/ai-proxy/values.yaml` must point to an Ollama endpoint reachable from the pod network; keep mock mode as the deterministic fallback.
- **OIDC failures:** confirm the AWS GitHub OIDC provider URL is `https://token.actions.githubusercontent.com`, its client ID list contains `sts.amazonaws.com`, `AWS_ROLE_ARN` matches the Terraform output, and the role trust subject matches this repository's immutable `main`-branch subject. The workflow does not use static AWS access keys.
