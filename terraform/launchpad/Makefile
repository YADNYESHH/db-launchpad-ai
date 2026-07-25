###############################################################################
# Convenience wrapper for the LaunchPad AI Terraform stack.
#
#   make init         PROJECT=my-proj
#   make plan         PROJECT=my-proj ENV=dev
#   make apply        PROJECT=my-proj ENV=dev
#   make image        PROJECT=my-proj            # build+push app image
#   make deploy-image PROJECT=my-proj            # roll a new Cloud Run revision
#   make destroy      PROJECT=my-proj ENV=dev
###############################################################################
ENV     ?= dev
REGION  ?= europe-west1
SERVICE ?= launchpad-ai
REPO    ?= launchpad-ai
TAG     ?= latest
VARFILE  = environments/$(ENV).tfvars
IMAGE    = $(REGION)-docker.pkg.dev/$(PROJECT)/$(REPO)/$(SERVICE):$(TAG)
# Path to the app/ directory (this module lives at terraform/launchpad/).
APP_DIR ?= ../../app

.PHONY: guard init fmt validate plan apply destroy output image deploy-image

guard:
	@test -n "$(PROJECT)" || (echo "ERROR: set PROJECT=your-gcp-project-id" && exit 1)

init: guard
	terraform init

fmt:
	terraform fmt -recursive

validate:
	terraform validate

plan: guard
	terraform plan -var project_id=$(PROJECT) -var-file=$(VARFILE)

apply: guard
	terraform apply -var project_id=$(PROJECT) -var-file=$(VARFILE)

destroy: guard
	terraform destroy -var project_id=$(PROJECT) -var-file=$(VARFILE)

output:
	terraform output

# Build & push the application image to Artifact Registry.
image: guard
	gcloud auth configure-docker $(REGION)-docker.pkg.dev --quiet
	docker build -t $(IMAGE) $(APP_DIR)
	docker push $(IMAGE)

# Roll a new Cloud Run revision using the pushed image (image is TF-ignored).
deploy-image: guard
	gcloud run deploy $(SERVICE) --image $(IMAGE) --region $(REGION) --project $(PROJECT)
