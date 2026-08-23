-- Telegram message ids are only unique *within* a channel, so a raw `id`
-- alone can't be a primary key once more than one channel has data (it
-- wasn't -- the old `unique` test on `id` was guaranteed to fail). We mint
-- a stable surrogate key from (channel, message_id) instead.
with source as (
    select * from {{ source('raw', 'telegram_messages') }}
    where message_id is not null
),

renamed as (
    select
        {{ dbt_utils.generate_surrogate_key(['channel', 'message_id']) }} as message_key,
        channel,
        message_id,
        sent_at,
        sender_id,
        message_text,
        media_type,
        media_url,
        media_size_kb,
        width,
        height,
        length(coalesce(message_text, '')) as message_length,
        media_url is not null as has_media
    from source
)

select * from renamed
