###############################################################################
# Providers
#
# Credentials are supplied out-of-band (never in code):
#   - locally:  `gcloud auth application-default login`
#   - CI:       Workload Identity Federation (google-github-actions/auth)
# Optionally set `credentials` via the GOOGLE_CREDENTIALS env var.
###############################################################################
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
