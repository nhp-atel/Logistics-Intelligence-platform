{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'customers') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by customer_id
            order by _loaded_at desc
        ) as _row_num
    from source
),

cleaned as (
    select
        -- Primary key
        customer_id,

        -- Customer info
        lower(trim(customer_type)) as customer_type,
        trim(name) as name,
        lower(trim(email)) as email,
        regexp_replace(phone, r'[^0-9]', '') as phone_normalized,
        phone as phone_original,

        -- Address
        trim(address_street) as address_street,
        trim(address_city) as address_city,
        upper(trim(address_state)) as address_state,
        trim(address_zip_code) as address_zip_code,
        upper(trim(coalesce(address_country, 'US'))) as address_country,

        -- Account info
        created_at,
        date(created_at) as created_date,
        lower(trim(tier)) as tier,
        coalesce(is_active, true) as is_active,

        -- Metadata
        _loaded_at

    from deduplicated
    where _row_num = 1
        and customer_id is not null
)

select * from cleaned
