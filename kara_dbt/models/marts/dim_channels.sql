select distinct
    channel as channel_name
from {{ ref('stg_telegram_messages') }}
