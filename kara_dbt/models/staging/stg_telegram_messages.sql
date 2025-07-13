with source as (
    select * from raw.telegram_messages
),

renamed as (
    select
        id,
        date,
        sender_id,
        text,
        media_type,
        media_url,
        channel,
        length(text) as message_length,
        case when media_url is not null then true else false end as has_media
    from source
)

select * from renamed
