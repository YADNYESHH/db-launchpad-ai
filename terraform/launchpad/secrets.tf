###############################################################################
# Secret Manager — JWT signing key (JWT_SECRET_KEY)
#
# If no value is supplied, a strong 64-hex-char secret is generated and stored.
# The secret VALUE is never rendered in plan output beyond Terraform's normal
# sensitive handling, and should live in an encrypted remote state backend.
###############################################################################
resource "random_password" "jwt" {
  count   = var.jwt_secret_value == "" ? 1 : 0
  length  = 64
  special = false
}

resource "google_secret_manager_secret" "jwt" {
  project   = var.project_id
  secret_id = "${var.service_name}-jwt-secret"
  labels    = var.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "jwt" {
  secret      = google_secret_manager_secret.jwt.id
  secret_data = var.jwt_secret_value != "" ? var.jwt_secret_value : random_password.jwt[0].result
}

# Runtime SA may read the JWT secret (least privilege: secret-scoped, not project-wide).
resource "google_secret_manager_secret_iam_member" "jwt_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.jwt.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.runtime_sa_email}"
}
