# LaunchPad AI — Terraform (Cloud Run) Infrastructure

Self-contained, environment-agnostic Terraform that provisions **everything**
LaunchPad AI needs to run on Google Cloud, so you can deploy it into **any GCP
project** (a fresh personal project, a test env, or a platform-managed one).

It is a single root module: run `terraform` from **this directory**
(`terraform/launchpad/`). It does not conflict with the hackathon template files
in `terraform/` (which stay as-is).

---

## What it provisions

| Resource | Purpose |
|---|---|
| **Enabled APIs** | run, artifactregistry, firestore, aiplatform, secretmanager, iam, iamcredentials, cloudresourcemanager, serviceusage, sts, logging, monitoring |
| **Artifact Registry** (Docker) | Holds the app container image |
| **Firestore** (Native) | Production data store (`STORE_BACKEND=firestore`) |
| **Secret Manager** | `<service>-jwt-secret` → mounted as `JWT_SECRET_KEY` (auto-generated if not provided) |
| **Runtime service account** | Least-privilege identity Cloud Run runs as (Firestore user, Vertex AI user, log/metric writer, secret accessor) |
| **Cloud Run v2 service** | Serves the FastAPI API + built React SPA on port 8080, with health probes, scaling and secret env |
| **Public invoker** (optional) | `allUsers → roles/run.invoker` when `allow_unauthenticated = true` |
| **Workload Identity Federation** (optional) | Keyless GitHub Actions deploys (pool + provider + deployer SA), scoped to one repo |

The design mirrors the app's real runtime contract (see `app/Dockerfile` and
`app/backend/*`): env vars `STORE_BACKEND`, `PROJECT_ID`, `VERTEX_LOCATION`,
`VERTEX_MODEL`, `ALLOWED_ORIGINS`, `LIVE_SEED`, `BUILD_SHA`, and the
`JWT_SECRET_KEY` secret.

---

## Prerequisites

- Terraform >= 1.5, `gcloud`, and Docker (only if you build the image locally).
- A GCP project and billing enabled.
- Authenticate once:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  gcloud config set project YOUR_PROJECT_ID
  ```
- The identity you run Terraform as needs enough rights to create the resources
  above (e.g. Owner/Editor on a personal project, or the equivalent custom roles).

---

## Quick start (any GCP project)

```bash
cd terraform/launchpad

# 1) First apply — bootstraps infra with a placeholder image
terraform init
terraform apply -var project_id=YOUR_PROJECT_ID -var-file=environments/dev.tfvars

# 2) Build & push the real app image (from repo root context 'app/')
terraform output -raw docker_build_push_hint    # prints the exact commands
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker build -t "$(terraform output -raw image_reference)" ../../app
docker push  "$(terraform output -raw image_reference)"

# 3) Roll the new image onto Cloud Run
gcloud run deploy launchpad-ai \
  --image "$(terraform output -raw image_reference)" \
  --region europe-west1 --project YOUR_PROJECT_ID

# 4) Open it
terraform output -raw service_url
```

Or use the `Makefile`:
```bash
make init  PROJECT=YOUR_PROJECT_ID
make apply PROJECT=YOUR_PROJECT_ID ENV=dev
make image PROJECT=YOUR_PROJECT_ID
make deploy-image PROJECT=YOUR_PROJECT_ID
```

> **Why two steps for the image?** Terraform owns the *infrastructure*; the image
> tag is normally rolled by CI. The Cloud Run resource ignores changes to the
> running image (see `lifecycle` in `cloud_run.tf`) to avoid perpetual drift.
> For the very first apply on an empty project there is no image yet, so
> `use_bootstrap_image = true` deploys a public "hello" placeholder; flip it off
> (or just let CI/`deploy-image` roll your image) afterwards.

---

## Testing the deployment

```bash
URL=$(terraform output -raw service_url)
curl -s "$URL/api/health"          # -> {"status":"healthy",...,"version":"<tag>"}
open "$URL"                         # the full app (login: demo accounts, pw demo1234)
```
Demo accounts (password `demo1234`): `anna.schmidt@launchpad.demo` (RM),
`priya.nair@launchpad.demo` (Product Owner), `wei.chen@launchpad.demo`
(Control Reviewer), `admin@launchpad.demo` (Admin).

---

## Environments

`environments/dev.tfvars`, `staging.tfvars`, `prod.tfvars` capture sizing and
exposure per tier. Pass the project separately so the same files work anywhere:
```bash
terraform apply -var project_id=MY_PROJECT -var-file=environments/staging.tfvars
```
For real isolation, use a **separate GCP project and a separate state prefix**
per environment (see `backend.tf.example`).

---

## Remote state (recommended)

Copy `backend.tf.example` → `backend.tf`, set your bucket, then `terraform init`.
Create the versioned bucket once:
```bash
gcloud storage buckets create gs://YOUR-TFSTATE-BUCKET \
  --location=europe-west1 --uniform-bucket-level-access
gcloud storage buckets update gs://YOUR-TFSTATE-BUCKET --versioning
```

---

## Keyless CI with GitHub Actions (optional)

Enable Workload Identity Federation so GitHub Actions deploys with **no static
keys**:
```hcl
enable_github_wif = true
github_owner      = "YADNYESHH"
github_repo       = "db-launchpad-ai"
```
After apply, wire the outputs into your workflow's `google-github-actions/auth`:
```yaml
with:
  project_id: YOUR_PROJECT_ID
  workload_identity_provider: <terraform output wif_provider>
  service_account: <terraform output wif_deployer_service_account>
```

---

## Key variables

| Variable | Default | Notes |
|---|---|---|
| `project_id` | — | **Required** |
| `region` | `europe-west1` | Cloud Run / Artifact Registry / Vertex |
| `service_name` | `launchpad-ai` | Also the image name |
| `store_backend` | `firestore` | `memory` for an ephemeral demo |
| `vertex_model` | `gemini-2.5-flash` | Grounded discovery / prose / chat |
| `firestore_location_id` | `eur3` | Immutable; set `create_firestore_database=false` to reuse an existing DB |
| `min/max_instances` | `0`/`4` | Set `min>=1` to kill cold starts |
| `cpu` / `memory` | `1` / `512Mi` | Per instance |
| `allow_unauthenticated` | `true` | `false` = private (front with LB + IAP) |
| `jwt_secret_value` | `""` | Empty ⇒ auto-generate a strong secret |
| `create_runtime_service_account` | `true` | `false` + `runtime_service_account_email` to reuse a platform SA |
| `use_bootstrap_image` | `false` | `true` for first apply on an empty project |
| `enable_github_wif` | `false` | Keyless GitHub Actions deploys |

Run `terraform output` for URLs, SA emails, the image reference and (if enabled)
the WIF provider/deployer SA.

---

## Notes & guardrails

- **Least privilege**: the runtime SA gets only Firestore, Vertex AI, logging,
  monitoring and secret-scoped access. The CI deployer (WIF) gets only
  `run.admin` + `artifactregistry.writer` + `actAs` the runtime SA.
- **No secrets in code**: the JWT secret is generated/stored in Secret Manager;
  `terraform.tfvars` and `*.auto.tfvars` are git-ignored.
- **Safe destroy**: enabled APIs are not disabled on destroy; Firestore has
  delete-protection enabled and an `ABANDON` deletion policy to avoid data loss.
- **Same-origin app**: the SPA is served by the API, so `ALLOWED_ORIGINS` only
  matters for separately-hosted frontends.
