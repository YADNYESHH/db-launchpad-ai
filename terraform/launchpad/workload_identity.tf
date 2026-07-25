###############################################################################
# GitHub Actions → GCP Workload Identity Federation (optional, keyless CI)
#
# Enable with enable_github_wif = true and set github_owner / github_repo.
# Produces a deployer SA that GitHub Actions can impersonate with NO static
# keys, scoped to exactly one repository. Wire the outputs into the workflow's
# google-github-actions/auth step.
###############################################################################
resource "google_iam_workload_identity_pool" "github" {
  count = var.enable_github_wif ? 1 : 0

  project                   = var.project_id
  workload_identity_pool_id = "${var.service_name}-gh-pool"
  display_name              = "${var.service_name} GitHub pool"
  description               = "WIF pool for GitHub Actions deploying ${var.service_name}"

  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  count = var.enable_github_wif ? 1 : 0

  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github[0].workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  display_name                       = "GitHub OIDC"

  # Restrict federation to the specified repository only.
  attribute_condition = "assertion.repository == '${var.github_owner}/${var.github_repo}'"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Dedicated deployer identity for CI (separate from the runtime identity).
resource "google_service_account" "deployer" {
  count = var.enable_github_wif ? 1 : 0

  project      = var.project_id
  account_id   = "${var.service_name}-deployer"
  display_name = "${var.service_name} CI deployer"

  depends_on = [google_project_service.apis]
}

# Least-privilege deploy roles: push images + deploy revisions + act as runtime SA.
resource "google_project_iam_member" "deployer_roles" {
  for_each = var.enable_github_wif ? toset([
    "roles/run.admin",
    "roles/artifactregistry.writer",
  ]) : toset([])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deployer[0].email}"
}

# Deployer must be able to actAs the runtime SA to deploy a revision that runs as it.
resource "google_service_account_iam_member" "deployer_actas_runtime" {
  count = var.enable_github_wif ? 1 : 0

  service_account_id = "projects/${var.project_id}/serviceAccounts/${local.runtime_sa_email}"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer[0].email}"
}

# Allow the specific GitHub repo to impersonate the deployer SA via the WIF pool.
resource "google_service_account_iam_member" "deployer_wif_binding" {
  count = var.enable_github_wif ? 1 : 0

  service_account_id = google_service_account.deployer[0].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github[0].name}/attribute.repository/${var.github_owner}/${var.github_repo}"
}
