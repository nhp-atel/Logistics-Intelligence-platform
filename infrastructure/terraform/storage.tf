# Cloud Storage Buckets

# Raw data landing zone
resource "google_storage_bucket" "raw_data" {
  name          = "${var.project_id}-raw-data"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.data_retention_days
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = local.labels

  depends_on = [google_project_service.services]
}

# Staging data
resource "google_storage_bucket" "staging_data" {
  name          = "${var.project_id}-staging-data"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = false
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  labels = local.labels

  depends_on = [google_project_service.services]
}

# Processed data
resource "google_storage_bucket" "processed_data" {
  name          = "${var.project_id}-processed-data"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  labels = local.labels

  depends_on = [google_project_service.services]
}

# Airflow DAGs bucket
resource "google_storage_bucket" "airflow_dags" {
  name          = "${var.project_id}-airflow-dags"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  labels = local.labels

  depends_on = [google_project_service.services]
}

# Terraform state bucket (if needed)
resource "google_storage_bucket" "terraform_state" {
  count = var.environment == "prod" ? 1 : 0

  name          = "${var.project_id}-terraform-state"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  labels = local.labels

  depends_on = [google_project_service.services]
}

# Bucket IAM bindings

resource "google_storage_bucket_iam_member" "raw_data_airflow" {
  bucket = google_storage_bucket.raw_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_storage_bucket_iam_member" "raw_data_pipeline" {
  bucket = google_storage_bucket.raw_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.data_pipeline.email}"
}

resource "google_storage_bucket_iam_member" "staging_data_airflow" {
  bucket = google_storage_bucket.staging_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_storage_bucket_iam_member" "processed_data_airflow" {
  bucket = google_storage_bucket.processed_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_storage_bucket_iam_member" "dags_airflow" {
  bucket = google_storage_bucket.airflow_dags.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.airflow.email}"
}
