variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "bigquery_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "US"
}

variable "enable_composer" {
  description = "Enable Cloud Composer (expensive - disable for cost savings)"
  type        = bool
  default     = false
}

variable "composer_node_count" {
  description = "Number of nodes in Cloud Composer environment"
  type        = number
  default     = 3
}

variable "enable_vertex_ai" {
  description = "Enable Vertex AI Feature Store"
  type        = bool
  default     = false
}

variable "api_min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "api_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "data_retention_days" {
  description = "Number of days to retain raw data"
  type        = number
  default     = 365
}

variable "allowed_ingress" {
  description = "Allowed ingress for Cloud Run (all, internal, internal-and-cloud-load-balancing)"
  type        = string
  default     = "all"
}
