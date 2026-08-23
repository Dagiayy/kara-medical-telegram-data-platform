select distinct
    {{ dbt_utils.generate_surrogate_key(['channel']) }} as channel_id,
    channel as channel_name
from {{ ref('stg_telegram_messages') }}
