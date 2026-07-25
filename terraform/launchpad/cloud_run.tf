###############################################################################
# Cloud Run v2 service — serves the FastAPI API + built React SPA (port 8080)
#
# Env vars mirror the app's runtime contract (app/Dockerfile, backend/*):
#   STORE_BACKEND, PROJECT_ID, VERTEX_LOCATION, VERTEX_MODEL, ALLOWED_ORIGINS,
#   LIVE_SEED, BUILD_SHA  + JWT_SECRET_KEY (from Secret Manager).
###############################################################################
resource "google_cloud_run_v2_service" "app" {
  project             = var.project_id
  name                = var.service_name
  location            = var.region
  ingress             = var.ingress
  deletion_protection = false
  labels              = var.labels

  template {
    service_account                  = local.runtime_sa_email
    max_instance_request_concurrency = var.concurrency
    timeout                          = "${var.request_timeout_seconds}s"

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = local.effective_image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle          = var.min_instances == 0
        startup_cpu_boost = true
      }

      env {
        name  = "STORE_BACKEND"
        value = var.store_backend
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "VERTEX_LOCATION"
        value = local.vertex_location
      }
      env {
        name  = "VERTEX_MODEL"
        value = var.vertex_model
      }
      env {
        name  = "ALLOWED_ORIGINS"
        value = local.allowed_origins
      }
      env {
        name  = "LIVE_SEED"
        value = var.live_seed ? "true" : "false"
      }
      env {
        name  = "BUILD_SHA"
        value = var.image_tag
      }
      env {
        name = "JWT_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        initial_delay_seconds = 5
        period_seconds        = 5
        timeout_seconds       = 3
        failure_threshold     = 10
        http_get {
          path = "/api/health"
          port = 8080
        }
      }

      liveness_probe {
        period_seconds = 30
        http_get {
          path = "/api/health"
          port = 8080
        }
      }
    }
  }

  # Terraform owns the infrastructure; CI rolls the image tag out-of-band.
  # Ignoring image (and the client tags Cloud Run stamps on deploy) prevents
  # perpetual drift between Terraform and the CI-deployed revision.
  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image,
    ]
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_iam_member.jwt_accessor,
    google_project_iam_member.runtime_roles,
  ]
}

# Public exposure (allow-unauthenticated). Toggle with allow_unauthenticated.
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
