###############################################################################
# Outputs
###############################################################################
output "service_url" {
  description = "Public HTTPS URL of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.app.uri
}

output "service_name" {
  description = "Cloud Run service name."
  value       = google_cloud_run_v2_service.app.name
}

output "region" {
  description = "Deployment region."
  value       = var.region
}

output "runtime_service_account_email" {
  description = "Identity the Cloud Run service runs as."
  value       = local.runtime_sa_email
}

output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository path."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "image_reference" {
  description = "Computed Artifact Registry image reference for the app."
  value       = local.ar_image
}

output "jwt_secret_id" {
  description = "Secret Manager secret ID holding the JWT signing key."
  value       = google_secret_manager_secret.jwt.secret_id
}

output "firestore_database" {
  description = "Firestore database name (empty if not managed here)."
  value       = var.create_firestore_database ? google_firestore_database.default[0].name : "(not managed by this stack)"
}

# ---- Workload Identity Federation (only when enabled) -----------------------
output "wif_provider" {
  description = "Full WIF provider resource name for google-github-actions/auth (workload_identity_provider)."
  value       = var.enable_github_wif ? google_iam_workload_identity_pool_provider.github[0].name : null
}

output "wif_deployer_service_account" {
  description = "Deployer SA email GitHub Actions should impersonate."
  value       = var.enable_github_wif ? google_service_account.deployer[0].email : null
}

# ---- Handy build/push/deploy commands --------------------------------------
output "docker_build_push_hint" {
  description = "One-liner to build & push the app image (run from repo root)."
  value       = "gcloud auth configure-docker ${var.region}-docker.pkg.dev && docker build -t ${local.ar_image} app && docker push ${local.ar_image}"
}
