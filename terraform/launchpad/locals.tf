###############################################################################
# Locals — computed values used across the module
###############################################################################
locals {
  # Vertex AI location falls back to the primary region when not set.
  vertex_location = var.vertex_location != "" ? var.vertex_location : var.region

  # Fully-qualified image path in Artifact Registry.
  ar_image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository}/${var.service_name}:${var.image_tag}"

  # Which image the Cloud Run service is created with.
  #   - explicit override wins
  #   - else the bootstrap placeholder (first apply, before your image exists)
  #   - else the computed Artifact Registry path
  effective_image = var.container_image != "" ? var.container_image : (var.use_bootstrap_image ? var.bootstrap_image : local.ar_image)

  # Runtime service account email (created here or reused).
  runtime_sa_email = var.create_runtime_service_account ? google_service_account.runtime[0].email : var.runtime_service_account_email

  # CORS: same-origin in prod; always allow local dev; plus any extras.
  allowed_origins = join(",", distinct(concat(
    ["http://localhost:5173", "http://127.0.0.1:5173"],
    var.allowed_origins_extra,
  )))

  # Google APIs the app needs to run and be deployed.
  required_apis = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "sts.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]

  # Project-level roles granted to the runtime service account.
  runtime_roles = [
    "roles/datastore.user",          # Firestore read/write
    "roles/aiplatform.user",         # Vertex AI Gemini calls
    "roles/logging.logWriter",       # structured logs
    "roles/monitoring.metricWriter", # runtime metrics
  ]
}
