select
    id as message_id,
    channel,
    date::date as date_id,
    sender_id,
    message_length,
    has_media,
    media_type
from {{ ref('stg_telegram_messages') }}
