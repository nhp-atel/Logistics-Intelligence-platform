# Architecture Documentation

## Overview

This document describes the architecture of the Logistics Data Platform, a production-grade data engineering solution for package delivery analytics.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│  Packages   │  Tracking   │  Weather    │  Customers/Locations  │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬────────────────┘
       │             │             │             │
       ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                              │
│  Cloud Storage (batch) │ Pub/Sub (streaming) │ API pulls        │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│               ORCHESTRATION (Cloud Composer/Airflow)             │
│  Ingestion DAGs → Transform DAGs → Quality DAGs → Feature DAGs  │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   TRANSFORMATION (dbt)                           │
│  Raw → Staging → Intermediate → Marts (Facts/Dims) → Features   │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA WAREHOUSE (BigQuery)                     │
│  raw.* │ staging.* │ warehouse.* │ features.*                   │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVING LAYER                               │
│  FastAPI (Cloud Run) │ Looker Studio │ Jupyter Notebooks        │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Data Sources

1. **Package Orders**: Core shipment records with sender, recipient, dimensions, service type
2. **Tracking Events**: Real-time package scan events (pickup, transit, delivery)
3. **Weather Data**: External weather API integration for delay prediction
4. **Master Data**: Customers, locations, drivers, vehicles

### Ingestion Layer

- **Batch Ingestion**: GCS file uploads processed by Airflow sensors
- **Streaming Ingestion**: Pub/Sub for real-time tracking events
- **API Pulls**: Scheduled weather data fetching

### Orchestration

Cloud Composer (managed Airflow) coordinates all pipelines:

| DAG | Schedule | Purpose |
|-----|----------|---------|
| `ingest_raw_packages` | Daily 6 AM | Load package data from GCS |
| `ingest_tracking_events` | Every 30 min | Load tracking events |
| `ingest_weather_data` | Daily 5 AM | Fetch weather from API |
| `raw_to_staging` | 3x daily | Basic transformations |
| `run_dbt_models` | Daily 7 AM | Full dbt pipeline |
| `data_quality_checks` | Daily 8 AM | Great Expectations validation |
| `compute_features` | Daily 9 AM | ML feature computation |

### Transformation Layer

dbt models organized in layers:

1. **Staging**: Clean and standardize raw data
   - Deduplication
   - Type casting
   - Null handling

2. **Intermediate**: Business logic
   - Enriched deliveries
   - Customer metrics aggregation

3. **Marts**: Dimensional model
   - Fact tables (deliveries, tracking_events)
   - Dimension tables (customers, locations, drivers, date)

4. **Features**: ML-ready tables
   - Delivery prediction features
   - Customer segmentation features
   - Route performance features

### Data Warehouse

BigQuery datasets:

| Dataset | Purpose | Retention |
|---------|---------|-----------|
| `raw` | Landing zone | 365 days |
| `staging` | Cleaned data | 90 days |
| `warehouse` | Dimensional model | Permanent |
| `features` | ML features | 90 days |

### Serving Layer

- **FastAPI**: REST API for data access
- **Cloud Run**: Serverless deployment
- **Looker Studio**: Business dashboards
- **Jupyter**: Ad-hoc analysis

## Data Flow

### Batch Pipeline

```
GCS Upload → Sensor Detection → Load to raw.* →
dbt staging → dbt intermediate → dbt marts →
Quality Checks → Feature Computation
```

### Streaming Pipeline

```
Pub/Sub Event → BigQuery Streaming Insert →
raw.tracking_events_stream → Merge to main table
```

## Security

### Authentication

- Service accounts with least-privilege IAM
- API key authentication for REST API
- VPC Service Controls (production)

### Data Protection

- Encryption at rest (BigQuery, GCS)
- Encryption in transit (TLS)
- Column-level security for PII (future)

## Scalability

### Horizontal Scaling

- Cloud Run auto-scales API instances
- Airflow workers scale with workload
- BigQuery scales automatically

### Data Partitioning

- `fact_deliveries`: Partitioned by `created_date`
- `fact_tracking_events`: Partitioned by `event_date`
- Clustering on frequently filtered columns

## Monitoring

### Metrics

- Pipeline success/failure rates
- Data freshness SLAs
- Query performance
- API latency

### Alerting

- Airflow task failures → Email/Slack
- Data quality failures → Pub/Sub → Alert channel
- API errors → Cloud Monitoring

## Disaster Recovery

### Backup Strategy

- BigQuery: 7-day time travel + daily exports
- GCS: Versioning enabled
- Terraform state: Remote backend with versioning

### Recovery Procedures

1. Point-in-time recovery for BigQuery
2. Restore from GCS backups
3. Terraform for infrastructure recreation

## Cost Management

### Optimization Strategies

1. **BigQuery**: Partitioning, clustering, materialized views
2. **Storage**: Lifecycle policies, compression
3. **Compute**: Auto-scaling, preemptible workers
4. **Development**: Local Docker environment

### Budget Alerts

- Monthly budget alerts at 50%, 80%, 100%
- Per-service cost tracking
- Query cost estimation
