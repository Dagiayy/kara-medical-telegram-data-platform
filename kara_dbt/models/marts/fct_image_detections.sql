-- `raw.image_detections` is written directly by kara_detection.detect_images
-- (Python owns that operational table). This mart is a plain read + key
-- resolution on top of it -- dbt never creates or writes raw.image_detections
-- itself, which is what the previous version of this file tried to do (a
-- bare CREATE TABLE statement dbt would have wrapped in another CREATE
-- TABLE AS, guaranteed to fail on `dbt run`).
select
    rid.detection_id,
    rid.image_id,
    s.message_key as message_id,
    rid.channel,
    rid.detected_object_class,
    rid.confidence_score,
    rid.detected_at
from {{ source('raw', 'image_detections') }} rid
left join {{ ref('stg_telegram_messages') }} s
    on s.channel = rid.channel and s.message_id = rid.message_id
