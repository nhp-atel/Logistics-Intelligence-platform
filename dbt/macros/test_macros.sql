{% test positive_value(model, column_name) %}

select *
from {{ model }}
where {{ column_name }} < 0

{% endtest %}


{% test valid_email(model, column_name) %}

select *
from {{ model }}
where {{ column_name }} is not null
    and not regexp_contains({{ column_name }}, r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

{% endtest %}


{% test valid_us_state(model, column_name) %}

{% set valid_states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
] %}

select *
from {{ model }}
where {{ column_name }} is not null
    and {{ column_name }} not in (
        {% for state in valid_states %}
            '{{ state }}'{% if not loop.last %},{% endif %}
        {% endfor %}
    )

{% endtest %}


{% test transit_time_reasonable(model, column_name) %}

-- Transit time should be between 0 and 720 hours (30 days)
select *
from {{ model }}
where {{ column_name }} is not null
    and ({{ column_name }} < 0 or {{ column_name }} > 720)

{% endtest %}
