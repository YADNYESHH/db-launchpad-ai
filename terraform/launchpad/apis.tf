###############################################################################
# Enable required Google APIs
#
# `disable_on_destroy = false` so a `terraform destroy` of this stack never
# tears down APIs that other workloads in the project may also rely on.
###############################################################################
resource "google_project_service" "apis" {
  for_each = var.enable_apis ? toset(local.required_apis) : toset([])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
