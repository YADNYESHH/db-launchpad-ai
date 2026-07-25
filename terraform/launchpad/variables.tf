###############################################################################
# Input variables
#
# Only `project_id` is strictly required. Everything else has sensible,
# production-minded defaults that match the app's runtime contract
# (see app/Dockerfile and app/backend/*). Override per environment with a
# tfvars file in ./environments or your own -var-file.
###############################################################################

# ---- Core -------------------------------------------------------------------
variable "project_id" {
  description = "Target GCP project ID to deploy LaunchPad AI into."
  type        = string
}

variable "region" {
  description = "Primary GCP region for Cloud Run, Artifact Registry and Vertex AI."
  type        = string
  default     = "europe-west1"
}

variable "labels" {
  description = "Common resource labels applied to all supported resources."
  type        = map(string)
  default = {
    app        = "launchpad-ai"
    managed-by = "terraform"
  }
}

variable "enable_apis" {
  description = "Whether Terraform should enable the required Google APIs. Set false if a platform team manages API enablement centrally."
  type        = bool
  default     = true
}

# ---- Naming -----------------------------------------------------------------
variable "service_name" {
  description = "Cloud Run service name (also used as the image name)."
  type        = string
  default     = "launchpad-ai"
}

variable "artifact_registry_repository" {
  description = "Artifact Registry Docker repository ID that holds the app image."
  type        = string
  default     = "launchpad-ai"
}

# ---- Container image --------------------------------------------------------
variable "container_image" {
  description = <<-EOT
    Full container image reference to deploy. Leave empty to use the computed
    Artifact Registry path `<region>-docker.pkg.dev/<project>/<repo>/<service>:<tag>`.
    Terraform owns the infrastructure; the image tag is normally rolled by CI,
    so changes to the running image are ignored (see lifecycle in cloud_run.tf).
  EOT
  type        = string
  default     = ""
}

variable "image_tag" {
  description = "Image tag to deploy when `container_image` is empty."
  type        = string
  default     = "latest"
}

variable "bootstrap_image" {
  description = "Public placeholder image used for the very first apply before your app image exists in Artifact Registry."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "use_bootstrap_image" {
  description = "If true, deploy `bootstrap_image` first (chicken-and-egg bootstrap). Flip to false once your real image is pushed, or just let CI update the image."
  type        = bool
  default     = false
}

# ---- Runtime configuration (maps to app env vars) ---------------------------
variable "store_backend" {
  description = "Persistence backend the app uses. 'firestore' for real deployments; 'memory' for ephemeral demos."
  type        = string
  default     = "firestore"

  validation {
    condition     = contains(["firestore", "memory"], var.store_backend)
    error_message = "store_backend must be either 'firestore' or 'memory'."
  }
}

variable "vertex_location" {
  description = "Vertex AI location. Defaults to `region` when empty."
  type        = string
  default     = ""
}

variable "vertex_model" {
  description = "Vertex AI Gemini model used for grounded discovery, prose and chat."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "live_seed" {
  description = "When true, the app attempts a live grounded seed of real companies on startup (falls back to synthetic)."
  type        = bool
  default     = false
}

variable "allowed_origins_extra" {
  description = "Extra CORS origins (the app is same-origin in prod, so this is only for separately-hosted frontends). localhost dev origins are always included."
  type        = list(string)
  default     = []
}

# ---- Cloud Run sizing & exposure -------------------------------------------
variable "cpu" {
  description = "vCPU per Cloud Run instance."
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory per Cloud Run instance."
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimum Cloud Run instances (set >=1 to avoid cold starts)."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum Cloud Run instances."
  type        = number
  default     = 4
}

variable "concurrency" {
  description = "Max concurrent requests per instance."
  type        = number
  default     = 80
}

variable "request_timeout_seconds" {
  description = "Cloud Run request timeout (seconds)."
  type        = number
  default     = 60
}

variable "allow_unauthenticated" {
  description = "Expose the service publicly (grant run.invoker to allUsers). Set false to keep it private behind IAM/IAP/LB."
  type        = bool
  default     = true
}

variable "ingress" {
  description = "Cloud Run ingress setting: INGRESS_TRAFFIC_ALL, INGRESS_TRAFFIC_INTERNAL_ONLY, or INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER."
  type        = string
  default     = "INGRESS_TRAFFIC_ALL"
}

# ---- Firestore --------------------------------------------------------------
variable "create_firestore_database" {
  description = "Create the Firestore (Native) database. Set false if it already exists in the project (only one default DB is allowed)."
  type        = bool
  default     = true
}

variable "firestore_location_id" {
  description = "Firestore location (multi-region like 'eur3'/'nam5' or a single region like 'europe-west1'). Immutable once created."
  type        = string
  default     = "eur3"
}

# ---- Secrets ----------------------------------------------------------------
variable "jwt_secret_value" {
  description = "JWT signing secret. Leave empty to auto-generate a strong random secret (recommended). NEVER commit a real value."
  type        = string
  default     = ""
  sensitive   = true
}

# ---- Runtime service account ------------------------------------------------
variable "create_runtime_service_account" {
  description = "Create a dedicated runtime service account for Cloud Run. Set false to reuse an existing one (e.g. a platform-provided workload SA)."
  type        = bool
  default     = true
}

variable "runtime_service_account_email" {
  description = "Existing runtime SA email to reuse when create_runtime_service_account = false."
  type        = string
  default     = ""
}

# ---- GitHub Actions Workload Identity Federation (optional) -----------------
variable "enable_github_wif" {
  description = "Provision a Workload Identity pool/provider + deployer SA so GitHub Actions can deploy with no static keys."
  type        = bool
  default     = false
}

variable "github_owner" {
  description = "GitHub org/user that owns the repo allowed to authenticate via WIF."
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name allowed to authenticate via WIF (without owner)."
  type        = string
  default     = ""
}
