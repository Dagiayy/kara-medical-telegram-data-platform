select distinct
    sent_at::date as date_id,
    extract(year from sent_at)::int as year,
    extract(month from sent_at)::int as month,
    extract(day from sent_at)::int as day,
    trim(to_char(sent_at, 'Day')) as weekday,
    extract(isodow from sent_at) in (6, 7) as is_weekend
from {{ ref('stg_telegram_messages') }}
where sent_at is not null
