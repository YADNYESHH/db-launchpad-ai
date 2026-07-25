###############################################################################
# Runtime service account + least-privilege IAM
#
# The Cloud Run service runs as this identity. It is created here by default,
# or reuse an existing SA (e.g. a platform-provided workload SA) by setting
# create_runtime_service_account = false and runtime_service_account_email.
###############################################################################
resource "google_service_account" "runtime" {
  count = var.create_runtime_service_account ? 1 : 0

  project      = var.project_id
  account_id   = "${var.service_name}-run"
  display_name = "${var.service_name} Cloud Run runtime"

  depends_on = [google_project_service.apis]
}

# Project-level roles for the runtime identity (Firestore, Vertex AI, logs, metrics).
resource "google_project_iam_member" "runtime_roles" {
  for_each = toset(local.runtime_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${local.runtime_sa_email}"
}
