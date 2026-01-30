# Pub/Sub Topics and Subscriptions

# Tracking events topic (for real-time streaming)
resource "google_pubsub_topic" "tracking_events" {
  name = "tracking-events"

  labels = local.labels

  message_retention_duration = "86400s" # 24 hours

  depends_on = [google_project_service.services]
}

# Dead letter topic for tracking events
resource "google_pubsub_topic" "tracking_events_dlq" {
  name = "tracking-events-dlq"

  labels = local.labels

  depends_on = [google_project_service.services]
}

# Subscription for BigQuery streaming
resource "google_pubsub_subscription" "tracking_events_bq" {
  name  = "tracking-events-bq-sub"
  topic = google_pubsub_topic.tracking_events.name

  labels = local.labels

  # BigQuery subscription
  bigquery_config {
    table          = "${var.project_id}.${google_bigquery_dataset.raw.dataset_id}.tracking_events_stream"
    write_metadata = true
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.tracking_events_dlq.id
    max_delivery_attempts = 5
  }

  depends_on = [
    google_bigquery_table.raw_tracking_events_stream,
    google_project_iam_member.pubsub_bq_metadata_viewer,
    google_project_iam_member.pubsub_bq_data_editor,
  ]
}

# Table for streaming data
resource "google_bigquery_table" "raw_tracking_events_stream" {
  dataset_id = google_bigquery_dataset.raw.dataset_id
  table_id   = "tracking_events_stream"

  time_partitioning {
    type  = "DAY"
    field = "event_timestamp"
  }

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
  ])

  deletion_protection = false
}

# Subscription for processing pipeline
resource "google_pubsub_subscription" "tracking_events_processing" {
  name  = "tracking-events-processing-sub"
  topic = google_pubsub_topic.tracking_events.name

  labels = local.labels

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.tracking_events_dlq.id
    max_delivery_attempts = 5
  }

  expiration_policy {
    ttl = "2678400s" # 31 days
  }
}

# Data quality alerts topic
resource "google_pubsub_topic" "data_quality_alerts" {
  name = "data-quality-alerts"

  labels = local.labels

  depends_on = [google_project_service.services]
}

# Subscription for data quality alerts
resource "google_pubsub_subscription" "data_quality_alerts" {
  name  = "data-quality-alerts-sub"
  topic = google_pubsub_topic.data_quality_alerts.name

  labels = local.labels

  ack_deadline_seconds = 30

  expiration_policy {
    ttl = "2678400s" # 31 days
  }
}

# Pipeline completion notifications
resource "google_pubsub_topic" "pipeline_notifications" {
  name = "pipeline-notifications"

  labels = local.labels

  depends_on = [google_project_service.services]
}

# IAM for Pub/Sub to write to BigQuery
data "google_project" "current" {}

resource "google_project_iam_member" "pubsub_bq_metadata_viewer" {
  project = var.project_id
  role    = "roles/bigquery.metadataViewer"
  member  = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "pubsub_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}
