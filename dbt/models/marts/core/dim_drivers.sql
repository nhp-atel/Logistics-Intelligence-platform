{{
    config(
        materialized='table'
    )
}}

with drivers as (
    select * from {{ source('raw', 'drivers') }}
),

deduplicated as (
    select
        *,
        row_number() over (partition by driver_id order by _loaded_at desc) as _row_num
    from drivers
),

final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['driver_id']) }} as driver_key,

        -- Natural key
        driver_id,

        -- Attributes
        concat(first_name, ' ', last_name) as full_name,
        first_name,
        last_name,
        license_number,
        license_state,
        hire_date,
        home_facility_id,
        lower(status) as status,
        phone,
        email,
        years_experience,
        certifications,

        -- Derived
        case
            when status = 'active' then true
            else false
        end as is_active

    from deduplicated
    where _row_num = 1
)

select * from final
