# BigQuery Datasets

# Raw data landing zone
resource "google_bigquery_dataset" "raw" {
  dataset_id    = "raw"
  friendly_name = "Raw Data"
  description   = "Landing zone for raw ingested data"
  location      = var.bigquery_location

  labels = local.labels

  default_table_expiration_ms = var.data_retention_days * 24 * 60 * 60 * 1000

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "WRITER"
    user_by_email = google_service_account.airflow.email
  }

  access {
    role          = "WRITER"
    user_by_email = google_service_account.data_pipeline.email
  }

  depends_on = [google_project_service.services]
}

# Staging data (cleaned/validated)
resource "google_bigquery_dataset" "staging" {
  dataset_id    = "staging"
  friendly_name = "Staging Data"
  description   = "Cleaned and validated data from dbt staging models"
  location      = var.bigquery_location

  labels = local.labels

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "WRITER"
    user_by_email = google_service_account.airflow.email
  }

  access {
    role          = "READER"
    user_by_email = google_service_account.api.email
  }

  depends_on = [google_project_service.services]
}

# Data warehouse (dimensional model)
resource "google_bigquery_dataset" "warehouse" {
  dataset_id    = "warehouse"
  friendly_name = "Data Warehouse"
  description   = "Dimensional model with facts and dimensions"
  location      = var.bigquery_location

  labels = local.labels

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "WRITER"
    user_by_email = google_service_account.airflow.email
  }

  access {
    role          = "READER"
    user_by_email = google_service_account.api.email
  }

  depends_on = [google_project_service.services]
}

# Feature store tables
resource "google_bigquery_dataset" "features" {
  dataset_id    = "features"
  friendly_name = "ML Features"
  description   = "Feature tables for machine learning"
  location      = var.bigquery_location

  labels = local.labels

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "WRITER"
    user_by_email = google_service_account.airflow.email
  }

  access {
    role          = "READER"
    user_by_email = google_service_account.api.email
  }

  depends_on = [google_project_service.services]
}

# Raw tables

resource "google_bigquery_table" "raw_packages" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "packages"

  time_partitioning {
    type  = "DAY"
    field = "created_at"
  }

  clustering = ["status", "service_type"]

  labels = local.labels

  schema = jsonencode([
    { name = "package_id", type = "STRING", mode = "REQUIRED" },
    { name = "tracking_number", type = "STRING", mode = "REQUIRED" },
    { name = "sender_customer_id", type = "STRING", mode = "REQUIRED" },
    { name = "recipient_customer_id", type = "STRING", mode = "REQUIRED" },
    { name = "origin_location_id", type = "STRING", mode = "REQUIRED" },
    { name = "destination_location_id", type = "STRING", mode = "REQUIRED" },
    { name = "weight_lbs", type = "FLOAT64", mode = "REQUIRED" },
    { name = "length_in", type = "FLOAT64", mode = "NULLABLE" },
    { name = "width_in", type = "FLOAT64", mode = "NULLABLE" },
    { name = "height_in", type = "FLOAT64", mode = "NULLABLE" },
    { name = "volume_cubic_in", type = "FLOAT64", mode = "NULLABLE" },
    { name = "service_type", type = "STRING", mode = "REQUIRED" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "estimated_delivery_date", type = "DATE", mode = "REQUIRED" },
    { name = "actual_delivery_date", type = "DATE", mode = "NULLABLE" },
    { name = "status", type = "STRING", mode = "REQUIRED" },
    { name = "shipping_cost", type = "FLOAT64", mode = "NULLABLE" },
    { name = "declared_value", type = "FLOAT64", mode = "NULLABLE" },
    { name = "signature_required", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "is_fragile", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "is_hazardous", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "special_instructions", type = "STRING", mode = "NULLABLE" },
    { name = "_loaded_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])

  deletion_protection = false
}

resource "google_bigquery_table" "raw_tracking_events" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "tracking_events"

  time_partitioning {
    type  = "DAY"
    field = "event_timestamp"
  }

  clustering = ["event_type", "package_id"]

  labels = local.labels

  schema = jsonencode([
    { name = "event_id", type = "STRING", mode = "REQUIRED" },
    { name = "package_id", type = "STRING", mode = "REQUIRED" },
    { name = "location_id", type = "STRING", mode = "NULLABLE" },
    { name = "event_type", type = "STRING", mode = "REQUIRED" },
    { name = "event_timestamp", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "driver_id", type = "STRING", mode = "NULLABLE" },
    { name = "vehicle_id", type = "STRING", mode = "NULLABLE" },
    { name = "notes", type = "STRING", mode = "NULLABLE" },
    { name = "latitude", type = "FLOAT64", mode = "NULLABLE" },
    { name = "longitude", type = "FLOAT64", mode = "NULLABLE" },
    { name = "_loaded_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])

  deletion_protection = false
}

resource "google_bigquery_table" "raw_customers" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "customers"

  labels = local.labels

  schema = jsonencode([
    { name = "customer_id", type = "STRING", mode = "REQUIRED" },
    { name = "customer_type", type = "STRING", mode = "REQUIRED" },
    { name = "name", type = "STRING", mode = "REQUIRED" },
    { name = "email", type = "STRING", mode = "NULLABLE" },
    { name = "phone", type = "STRING", mode = "NULLABLE" },
    { name = "address_street", type = "STRING", mode = "NULLABLE" },
    { name = "address_city", type = "STRING", mode = "NULLABLE" },
    { name = "address_state", type = "STRING", mode = "NULLABLE" },
    { name = "address_zip_code", type = "STRING", mode = "NULLABLE" },
    { name = "address_country", type = "STRING", mode = "NULLABLE" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "tier", type = "STRING", mode = "NULLABLE" },
    { name = "is_active", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "_loaded_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])

  deletion_protection = false
}

resource "google_bigquery_table" "raw_locations" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "locations"

  labels = local.labels

  schema = jsonencode([
    { name = "location_id", type = "STRING", mode = "REQUIRED" },
    { name = "location_type", type = "STRING", mode = "REQUIRED" },
    { name = "name", type = "STRING", mode = "NULLABLE" },
    { name = "address", type = "STRING", mode = "NULLABLE" },
    { name = "city", type = "STRING", mode = "NULLABLE" },
    { name = "state", type = "STRING", mode = "NULLABLE" },
    { name = "zip_code", type = "STRING", mode = "NULLABLE" },
    { name = "country", type = "STRING", mode = "NULLABLE" },
    { name = "latitude", type = "FLOAT64", mode = "NULLABLE" },
    { name = "longitude", type = "FLOAT64", mode = "NULLABLE" },
    { name = "timezone", type = "STRING", mode = "NULLABLE" },
    { name = "region", type = "STRING", mode = "NULLABLE" },
    { name = "is_active", type = "BOOLEAN", mode = "NULLABLE" },
    { name = "_loaded_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])

  deletion_protection = false
}

resource "google_bigquery_table" "raw_drivers" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "drivers"

  labels = local.labels

  schema = jsonencode([
    { name = "driver_id", type = "STRING", mode = "REQUIRED" },
    { name = "first_name", type = "STRING", mode = "REQUIRED" },
    { name = "last_name", type = "STRING", mode = "REQUIRED" },
    { name = "license_number", type = "STRING", mode = "NULLABLE" },
    { name = "license_state", type = "STRING", mode = "NULLABLE" },
    { name = "hire_date", type = "DATE", mode = "NULLABLE" },
    { name = "home_facility_id", type = "STRING", mode = "NULLABLE" },
    { name = "status", type = "STRING", mode = "NULLABLE" },
    { name = "phone", type = "STRING", mode = "NULLABLE" },
    { name = "email", type = "STRING", mode = "NULLABLE" },
    { name = "years_experience", type = "INT64", mode = "NULLABLE" },
    { name = "certifications", type = "STRING", mode = "NULLABLE" },
    { name = "_loaded_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])

  deletion_protection = false
}

resource "google_bigquery_table" "raw_vehicles" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "vehicles"

  labels = local.labels

  schema = jsonencode([
    { name = "vehicle_id", type = "STRING", mode = "REQUIRED" },
    { name = "vehicle_type", type = "STRING", mode = "REQUIRED" },
    { name = "make", type = "STRING", mode = "NULLABLE" },
    { name = "model", type = "STRING", mode = "NULLABLE" },
    { name = "year", type = "INT64", mode = "NULLABLE" },
    { name = "capacity_lbs", type = "FLOAT64", mode = "NULLABLE" },
    { name = "capacity_cubic_ft", type = "FLOAT64", mode = "NULLABLE" },
    { name = "assigned_facility_id", type = "STRING", mode = "NULLABLE" },
    { name = "license_plate", type = "STRING", mode = "NULLABLE" },
    { name = "vin", type = "STRING", mode = "NULLABLE" },
    { name = "fuel_type", type = "STRING", mode = "NULLABLE" },
    { name = "status", type = "STRING", mode = "NULLABLE" },
    { name = "last_maintenance_date", type = "DATE", mode = "NULLABLE" },
    { name = "mileage", type = "INT64", mode = "NULLABLE" },
    { name = "_loaded_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])

  deletion_protection = false
}

resource "google_bigquery_table" "raw_weather" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "weather"

  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  labels = local.labels

  schema = jsonencode([
    { name = "location_id", type = "STRING", mode = "REQUIRED" },
    { name = "date", type = "DATE", mode = "REQUIRED" },
    { name = "condition", type = "STRING", mode = "NULLABLE" },
    { name = "temperature_f", type = "FLOAT64", mode = "NULLABLE" },
    { name = "humidity_pct", type = "INT64", mode = "NULLABLE" },
    { name = "wind_speed_mph", type = "FLOAT64", mode = "NULLABLE" },
    { name = "precipitation_in", type = "FLOAT64", mode = "NULLABLE" },
    { name = "visibility_miles", type = "FLOAT64", mode = "NULLABLE" },
    { name = "delay_probability", type = "FLOAT64", mode = "NULLABLE" },
    { name = "expected_delay_hours", type = "FLOAT64", mode = "NULLABLE" },
    { name = "_loaded_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])

  deletion_protection = false
}
