# Dev environment — ephemeral, cost-lean, public demo.
# Usage:  terraform apply -var-file=environments/dev.tfvars -var project_id=YOUR_DEV_PROJECT
region                = "europe-west1"
service_name          = "launchpad-ai"
firestore_location_id = "eur3"

min_instances = 0
max_instances = 2
cpu           = "1"
memory        = "512Mi"

allow_unauthenticated = true
live_seed             = false
use_bootstrap_image   = true

labels = {
  app        = "launchpad-ai"
  env        = "dev"
  managed-by = "terraform"
}
