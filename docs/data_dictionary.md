# Data Dictionary

This document describes all tables and columns in the Logistics Data Platform.

## Raw Layer (`raw.*`)

### raw.packages

Core package/shipment records as ingested from source systems.

| Column | Type | Description |
|--------|------|-------------|
| package_id | STRING | Primary key, unique package identifier |
| tracking_number | STRING | Public tracking number for customers |
| sender_customer_id | STRING | Foreign key to customers table (sender) |
| recipient_customer_id | STRING | Foreign key to customers table (recipient) |
| origin_location_id | STRING | Foreign key to locations (origin) |
| destination_location_id | STRING | Foreign key to locations (destination) |
| weight_lbs | FLOAT64 | Package weight in pounds |
| length_in | FLOAT64 | Package length in inches |
| width_in | FLOAT64 | Package width in inches |
| height_in | FLOAT64 | Package height in inches |
| volume_cubic_in | FLOAT64 | Calculated volume |
| service_type | STRING | Service type (GROUND, EXPRESS, NEXT_DAY, FREIGHT) |
| created_at | TIMESTAMP | When package entered the system |
| estimated_delivery_date | DATE | Promised delivery date |
| actual_delivery_date | DATE | Actual delivery date (null if not delivered) |
| status | STRING | Current status |
| shipping_cost | FLOAT64 | Cost charged for shipping |
| declared_value | FLOAT64 | Declared value for insurance |
| signature_required | BOOLEAN | Whether signature is required |
| is_fragile | BOOLEAN | Fragile handling required |
| is_hazardous | BOOLEAN | Hazardous materials flag |
| special_instructions | STRING | Delivery instructions |
| _loaded_at | TIMESTAMP | When record was loaded |

### raw.tracking_events

Package tracking/scan events.

| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Primary key |
| package_id | STRING | Foreign key to packages |
| location_id | STRING | Foreign key to locations |
| event_type | STRING | Type of event (PICKED_UP, IN_TRANSIT, DELIVERED, etc.) |
| event_timestamp | TIMESTAMP | When event occurred |
| driver_id | STRING | Foreign key to drivers (if applicable) |
| vehicle_id | STRING | Foreign key to vehicles (if applicable) |
| notes | STRING | Event notes |
| latitude | FLOAT64 | GPS latitude |
| longitude | FLOAT64 | GPS longitude |
| _loaded_at | TIMESTAMP | When record was loaded |

### raw.customers

Customer information.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | STRING | Primary key |
| customer_type | STRING | business or residential |
| name | STRING | Customer/company name |
| email | STRING | Email address |
| phone | STRING | Phone number |
| address_street | STRING | Street address |
| address_city | STRING | City |
| address_state | STRING | State code |
| address_zip_code | STRING | ZIP code |
| address_country | STRING | Country code |
| created_at | TIMESTAMP | Account creation date |
| tier | STRING | Customer tier (bronze, silver, gold, platinum) |
| is_active | BOOLEAN | Active account flag |
| _loaded_at | TIMESTAMP | When record was loaded |

### raw.locations

Facilities and addresses.

| Column | Type | Description |
|--------|------|-------------|
| location_id | STRING | Primary key |
| location_type | STRING | hub, distribution_center, customer_address, pickup_point |
| name | STRING | Location name |
| address | STRING | Street address |
| city | STRING | City |
| state | STRING | State code |
| zip_code | STRING | ZIP code |
| country | STRING | Country code |
| latitude | FLOAT64 | GPS latitude |
| longitude | FLOAT64 | GPS longitude |
| timezone | STRING | Timezone identifier |
| region | STRING | Geographic region (northeast, southeast, etc.) |
| is_active | BOOLEAN | Active location flag |
| _loaded_at | TIMESTAMP | When record was loaded |

---

## Staging Layer (`staging.*`)

Cleaned and standardized versions of raw tables with:
- Deduplication applied
- Consistent casing (UPPER for codes, lower for categories)
- Null handling
- Basic validation
- Added `_transformed_at` timestamp

---

## Warehouse Layer (`warehouse.*`)

### warehouse.dim_customers

Customer dimension table with aggregated metrics.

| Column | Type | Description |
|--------|------|-------------|
| customer_key | STRING | Surrogate key |
| customer_id | STRING | Natural key |
| customer_type | STRING | business or residential |
| name | STRING | Customer name |
| tier | STRING | Customer tier |
| is_active | BOOLEAN | Active flag |
| lifetime_packages_sent | INT64 | Total packages sent |
| lifetime_spend | FLOAT64 | Total shipping spend |
| avg_order_value | FLOAT64 | Average order value |
| packages_sent_30d | INT64 | Packages in last 30 days |
| spend_30d | FLOAT64 | Spend in last 30 days |
| valid_from | TIMESTAMP | SCD validity start |
| valid_to | TIMESTAMP | SCD validity end |
| is_current | BOOLEAN | Current record flag |

### warehouse.dim_locations

Location dimension table.

| Column | Type | Description |
|--------|------|-------------|
| location_key | STRING | Surrogate key |
| location_id | STRING | Natural key |
| location_type | STRING | Type of location |
| name | STRING | Location name |
| city | STRING | City |
| state | STRING | State code |
| zip_code | STRING | ZIP code |
| country | STRING | Country code |
| latitude | FLOAT64 | GPS latitude |
| longitude | FLOAT64 | GPS longitude |
| timezone | STRING | Timezone |
| region | STRING | Geographic region |
| is_facility | BOOLEAN | Hub/DC flag |

### warehouse.dim_drivers

Driver dimension table.

| Column | Type | Description |
|--------|------|-------------|
| driver_key | STRING | Surrogate key |
| driver_id | STRING | Natural key |
| full_name | STRING | Driver full name |
| first_name | STRING | First name |
| last_name | STRING | Last name |
| license_number | STRING | License number |
| hire_date | DATE | Hire date |
| home_facility_id | STRING | Home facility |
| status | STRING | active, inactive, on_leave |
| years_experience | INT64 | Years of experience |

### warehouse.dim_date

Date dimension table.

| Column | Type | Description |
|--------|------|-------------|
| date_key | INT64 | YYYYMMDD key |
| full_date | DATE | Full date |
| year | INT64 | Year |
| quarter | INT64 | Quarter (1-4) |
| month | INT64 | Month (1-12) |
| month_name | STRING | Month name |
| week_of_year | INT64 | Week number |
| day_of_week | INT64 | Day of week (1-7) |
| day_name | STRING | Day name |
| is_weekend | BOOLEAN | Weekend flag |
| is_holiday | BOOLEAN | US holiday flag |
| fiscal_year | INT64 | Fiscal year |
| fiscal_quarter | INT64 | Fiscal quarter |

### warehouse.fact_deliveries

Delivery fact table (grain: one row per package).

| Column | Type | Description |
|--------|------|-------------|
| package_key | STRING | Surrogate key |
| package_id | STRING | Natural key |
| tracking_number | STRING | Tracking number |
| sender_customer_key | STRING | FK to dim_customers |
| recipient_customer_key | STRING | FK to dim_customers |
| origin_location_key | STRING | FK to dim_locations |
| destination_location_key | STRING | FK to dim_locations |
| driver_key | STRING | FK to dim_drivers |
| ship_date_key | INT64 | FK to dim_date (ship) |
| delivery_date_key | INT64 | FK to dim_date (delivery) |
| service_type | STRING | Service type |
| status | STRING | Delivery status |
| route_type | STRING | local, intrastate, interstate |
| weight_lbs | FLOAT64 | Package weight |
| volume_cubic_in | FLOAT64 | Package volume |
| transit_days | INT64 | Days in transit |
| actual_transit_hours | FLOAT64 | Hours in transit |
| shipping_cost | FLOAT64 | Shipping cost |
| declared_value | FLOAT64 | Declared value |
| total_tracking_events | INT64 | Number of events |
| exception_count | INT64 | Number of exceptions |
| is_on_time | BOOLEAN | Delivered on time |
| created_at | TIMESTAMP | Package created |
| estimated_delivery_date | DATE | Estimated delivery |
| actual_delivery_date | DATE | Actual delivery |

### warehouse.fact_tracking_events

Tracking event fact table (grain: one row per event).

| Column | Type | Description |
|--------|------|-------------|
| event_key | STRING | Surrogate key |
| event_id | STRING | Natural key |
| package_id | STRING | Package ID |
| location_key | STRING | FK to dim_locations |
| driver_key | STRING | FK to dim_drivers |
| event_date_key | INT64 | FK to dim_date |
| event_type | STRING | Event type |
| event_timestamp | TIMESTAMP | When event occurred |
| hours_since_last_event | FLOAT64 | Hours since previous event |
| location_state | STRING | State code |
| location_region | STRING | Region |
| latitude | FLOAT64 | GPS latitude |
| longitude | FLOAT64 | GPS longitude |

---

## Features Layer (`features.*`)

### features.ftr_delivery_predictions

Features for delivery time prediction ML model.

| Column | Type | Description |
|--------|------|-------------|
| package_id | STRING | Package identifier |
| weight_lbs | FLOAT64 | Package weight |
| volume_cubic_in | FLOAT64 | Package volume |
| service_type | STRING | Service type |
| origin_region | STRING | Origin region |
| destination_region | STRING | Destination region |
| day_of_week | INT64 | Day of week |
| is_weekend | BOOLEAN | Weekend flag |
| is_holiday | BOOLEAN | Holiday flag |
| is_peak_season | BOOLEAN | Peak season flag |
| route_avg_transit_hours_7d | FLOAT64 | 7-day avg transit for route |
| route_avg_transit_hours_30d | FLOAT64 | 30-day avg transit for route |
| route_on_time_rate_7d | FLOAT64 | 7-day on-time rate for route |
| actual_transit_hours | FLOAT64 | Target variable |

### features.ftr_customer_segments

Features for customer segmentation.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | STRING | Customer identifier |
| customer_type | STRING | business/residential |
| total_packages_30d | INT64 | Packages in 30 days |
| total_packages_90d | INT64 | Packages in 90 days |
| total_spend_30d | FLOAT64 | Spend in 30 days |
| total_spend_90d | FLOAT64 | Spend in 90 days |
| avg_order_value | FLOAT64 | Average order value |
| pct_express_shipments | FLOAT64 | % express shipments |
| days_since_last_order | INT64 | Recency |
| customer_value_score | FLOAT64 | RFM-based score (1-3) |
| churn_risk_score | FLOAT64 | Churn probability (0-1) |
| customer_segment | STRING | Segment label |

### features.ftr_route_performance

Route-level performance metrics.

| Column | Type | Description |
|--------|------|-------------|
| route_key | STRING | Composite key |
| origin_region | STRING | Origin region |
| destination_region | STRING | Destination region |
| service_type | STRING | Service type |
| total_packages | INT64 | Total packages |
| packages_7d | INT64 | Packages in 7 days |
| packages_30d | INT64 | Packages in 30 days |
| avg_transit_hours | FLOAT64 | Average transit time |
| median_transit_hours | FLOAT64 | Median transit time |
| p90_transit_hours | FLOAT64 | 90th percentile transit |
| on_time_rate | FLOAT64 | On-time delivery rate |
| exception_rate | FLOAT64 | Exception rate |
| avg_shipping_cost | FLOAT64 | Average cost |
| total_revenue | FLOAT64 | Total revenue |
| performance_tier | STRING | excellent/good/average/needs_improvement |
