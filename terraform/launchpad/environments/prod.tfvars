# Production environment — warm, resilient. Consider making it private and
# fronting it with an external HTTPS Load Balancer + IAP or Cloud Armor.
# Usage:  terraform apply -var-file=environments/prod.tfvars -var project_id=YOUR_PROD_PROJECT
region                = "europe-west1"
service_name          = "launchpad-ai"
firestore_location_id = "eur3"

min_instances = 2
max_instances = 10
cpu           = "2"
memory        = "1Gi"
concurrency   = 80

# For a real production posture keep this false and put a load balancer + IAP
# (or Cloud Armor) in front; flip to true only for an open demo.
allow_unauthenticated = true
ingress               = "INGRESS_TRAFFIC_ALL"

live_seed           = true
use_bootstrap_image = false

labels = {
  app        = "launchpad-ai"
  env        = "prod"
  managed-by = "terraform"
}
