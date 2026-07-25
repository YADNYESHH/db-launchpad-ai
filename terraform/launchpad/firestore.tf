###############################################################################
# Firestore (Native mode) — the app's production data store
#
# GCP allows exactly one default Firestore database per project. If the project
# already has one, set `create_firestore_database = false`.
# `location_id` is immutable after creation.
###############################################################################
resource "google_firestore_database" "default" {
  count = var.create_firestore_database ? 1 : 0

  project     = var.project_id
  name        = "(default)"
  location_id = var.firestore_location_id
  type        = "FIRESTORE_NATIVE"

  # Guardrails: prevent accidental data loss on delete/replace.
  delete_protection_state = "DELETE_PROTECTION_ENABLED"
  deletion_policy         = "ABANDON"

  depends_on = [google_project_service.apis]
}
