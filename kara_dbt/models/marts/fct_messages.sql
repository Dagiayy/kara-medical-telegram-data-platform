select
    s.message_key as message_id,
    s.channel,
    d.channel_id,
    s.sent_at,
    s.sent_at::date as date_id,
    s.sender_id,
    s.message_text,
    s.message_length,
    s.has_media,
    s.media_type,
    s.media_url
from {{ ref('stg_telegram_messages') }} s
left join {{ ref('dim_channels') }} d on d.channel_name = s.channel
