# Staging environment — warm, closer to prod, still public for validation.
# Usage:  terraform apply -var-file=environments/staging.tfvars -var project_id=YOUR_STAGING_PROJECT
region                = "europe-west1"
service_name          = "launchpad-ai"
firestore_location_id = "eur3"

min_instances = 1
max_instances = 6
cpu           = "1"
memory        = "1Gi"

allow_unauthenticated = true
live_seed             = true
use_bootstrap_image   = false

labels = {
  app        = "launchpad-ai"
  env        = "staging"
  managed-by = "terraform"
}
