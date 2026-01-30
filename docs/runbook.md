# Operational Runbook

This runbook contains procedures for operating and troubleshooting the Logistics Data Platform.

## Daily Operations

### Morning Checklist

1. **Check Airflow DAG status**
   - Open Airflow UI: http://localhost:8080 (or Cloud Composer URL)
   - Verify all scheduled DAGs completed successfully
   - Check for any failed or stuck tasks

2. **Verify data freshness**
   ```sql
   -- Check latest data in raw tables
   SELECT
     'packages' as table_name,
     MAX(_loaded_at) as last_load
   FROM raw.packages
   UNION ALL
   SELECT
     'tracking_events',
     MAX(_loaded_at)
   FROM raw.tracking_events;
   ```

3. **Check data quality reports**
   - Review Great Expectations validation results
   - Address any warnings or failures

### Weekly Tasks

1. **Review pipeline performance**
   - Check DAG execution times
   - Identify slow-running tasks
   - Review BigQuery slot usage

2. **Storage cleanup**
   ```bash
   # Remove old staging files
   gsutil rm -r gs://$BUCKET/staging/$(date -d "30 days ago" +%Y%m%d)/*
   ```

3. **Update statistics**
   - Refresh dbt documentation
   - Update monitoring dashboards

## Common Procedures

### Rerunning Failed DAGs

1. **Identify the failure**
   - Check Airflow task logs
   - Review error messages

2. **Fix the issue**
   - Data issues: Fix source data and re-upload
   - Code issues: Deploy fix and restart

3. **Clear and rerun**
   ```bash
   # Clear failed task
   airflow tasks clear -t <task_id> -d <dag_id> -s <start_date> -e <end_date>

   # Or rerun entire DAG
   airflow dags trigger <dag_id> --exec-date <date>
   ```

### Backfilling Data

```bash
# Backfill a date range
airflow dags backfill \
  -s 2024-01-01 \
  -e 2024-01-31 \
  ingest_raw_packages

# For dbt, use incremental flags
cd dbt && dbt run --full-refresh --select +fact_deliveries
```

### Deploying Changes

1. **dbt model changes**
   ```bash
   # Test locally
   dbt run --select <model> --profiles-dir .
   dbt test --select <model> --profiles-dir .

   # Deploy via CI/CD (merge to main)
   # Or manually:
   dbt run --select <model> --profiles-dir . --target prod
   ```

2. **DAG changes**
   - Update DAG files in airflow/dags/
   - DAGs auto-sync in Composer
   - For local: restart scheduler

3. **API changes**
   ```bash
   # Build and push new image
   make build-api
   make push-api

   # Deploy to Cloud Run
   gcloud run deploy logistics-api \
     --image gcr.io/$PROJECT_ID/logistics-api:latest \
     --region us-central1
   ```

### Scaling Resources

**BigQuery slots:**
```bash
# Check current usage
bq show --format=prettyjson --reservation $PROJECT_ID:US.default

# Request more slots (if using flat-rate)
# Or use on-demand pricing
```

**Cloud Run instances:**
```bash
# Update min/max instances
gcloud run services update logistics-api \
  --min-instances 2 \
  --max-instances 20 \
  --region us-central1
```

**Composer workers:**
```bash
# Scale workers (requires Composer restart)
# Update via Terraform or Console
```

## Troubleshooting

### Data Pipeline Issues

#### DAG Stuck in Running State

1. Check if task is actually running
2. Look for zombie workers
3. Clear the stuck task:
   ```bash
   airflow tasks clear -d <dag_id> -t <task_id> -s <date> -e <date>
   ```

#### Data Not Loading

1. Verify source files exist in GCS:
   ```bash
   gsutil ls gs://$BUCKET/raw/packages/
   ```
2. Check file format matches expected schema
3. Review ingestion DAG logs
4. Validate BigQuery permissions

#### dbt Model Failure

1. Check dbt logs: `dbt/logs/dbt.log`
2. Run model in isolation:
   ```bash
   dbt run --select <model> --debug
   ```
3. Check for schema changes in source
4. Validate SQL syntax

### Data Quality Issues

#### Unexpected Null Values

1. Identify source of nulls:
   ```sql
   SELECT * FROM raw.packages
   WHERE package_id IS NULL
   LIMIT 100;
   ```
2. Check data generation or source system
3. Add null handling in staging model

#### Duplicate Records

1. Find duplicates:
   ```sql
   SELECT package_id, COUNT(*) as cnt
   FROM raw.packages
   GROUP BY package_id
   HAVING cnt > 1;
   ```
2. Identify source (multiple loads, source duplication)
3. Add deduplication in staging

#### Referential Integrity Violations

1. Find orphaned records:
   ```sql
   SELECT p.package_id
   FROM raw.packages p
   LEFT JOIN raw.customers c ON p.sender_customer_id = c.customer_id
   WHERE c.customer_id IS NULL;
   ```
2. Load missing reference data
3. Or handle in transformation

### API Issues

#### 500 Internal Server Error

1. Check Cloud Run logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit 50
   ```
2. Common causes:
   - BigQuery connection failure
   - Missing environment variables
   - Code errors

#### Slow Response Times

1. Check BigQuery query performance
2. Add caching if appropriate
3. Optimize queries with indexes/clustering
4. Scale Cloud Run instances

#### Authentication Failures

1. Verify API key configuration
2. Check Secret Manager access
3. Review IAM permissions

### Infrastructure Issues

#### Terraform Apply Failures

1. Check for resource conflicts
2. Verify IAM permissions
3. Review error messages
4. Try targeted apply:
   ```bash
   terraform apply -target=google_bigquery_dataset.raw
   ```

#### Cloud Composer Issues

1. Check Composer environment health
2. Review worker logs
3. Check for resource exhaustion
4. Contact GCP support if persistent

## Monitoring Alerts

### Alert Response Procedures

| Alert | Severity | Response |
|-------|----------|----------|
| DAG failure | High | Check logs, rerun or fix |
| Data freshness | Medium | Investigate ingestion |
| API latency | Medium | Scale instances |
| BigQuery errors | High | Check query, permissions |
| Storage quota | Low | Clean up old data |

### Escalation Path

1. **Level 1**: On-call data engineer
2. **Level 2**: Data platform team lead
3. **Level 3**: GCP support (for infrastructure issues)

## Maintenance Windows

- **Daily**: 2-3 AM UTC (minimal impact)
- **Weekly**: Sunday 2-4 AM UTC (for major updates)
- **Monthly**: First Sunday, 12-4 AM UTC (for infrastructure changes)

## Disaster Recovery

### Data Recovery

1. **BigQuery time travel**:
   ```sql
   SELECT * FROM raw.packages
   FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);
   ```

2. **Restore from backup**:
   ```bash
   # List backups
   gsutil ls gs://$BUCKET-backups/

   # Restore to table
   bq load --source_format=PARQUET \
     raw.packages \
     gs://$BUCKET-backups/packages_20240101.parquet
   ```

### Infrastructure Recovery

```bash
# Recreate from Terraform
cd infrastructure/terraform
terraform apply -auto-approve
```

### Full Recovery Procedure

1. Verify infrastructure is healthy
2. Restore data from backups
3. Clear and rerun affected DAGs
4. Verify data quality
5. Resume normal operations
