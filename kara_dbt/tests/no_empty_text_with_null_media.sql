-- Singular test: fails if any message has neither text nor media -- such a
-- row would mean the scraper captured something it shouldn't have been
-- able to (Telegram messages always carry at least one of the two).
select *
from {{ ref('fct_messages') }}
where (message_text is null or message_text = '') and media_type is null
