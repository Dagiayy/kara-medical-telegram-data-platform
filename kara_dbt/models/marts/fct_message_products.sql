-- Deterministic, reviewable keyword matching against a curated seed
-- dictionary (kara_dbt/seeds/product_dictionary.csv) rather than an LLM:
-- product/brand mentions in these messages are a well-defined string-match
-- problem, so a dictionary is more accurate, free to run, fully
-- reproducible, and trivially auditable/extensible by a domain expert --
-- properties an LLM call would trade away for no real benefit here.
--
-- This is what backs the previously-nonexistent "top products" API
-- endpoint, which queried a `product_name` column that was never populated
-- by anything in the original project.
with messages as (
    select message_id, channel, message_text
    from {{ ref('fct_messages') }}
    where message_text is not null and message_text != ''
),

dictionary as (
    select * from {{ ref('product_dictionary') }}
)

select
    m.message_id,
    m.channel,
    d.product_name,
    d.category,
    d.keyword as matched_keyword
from messages m
inner join dictionary d
    on m.message_text ilike '%' || d.keyword || '%'
