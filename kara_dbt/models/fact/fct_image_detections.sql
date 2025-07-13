{{ config(materialized='table') }}

CREATE TABLE IF NOT EXISTS {{ this }} (
    detection_id SERIAL PRIMARY KEY,
    message_id INT NOT NULL,
    detected_object_class TEXT NOT NULL,
    confidence_score FLOAT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES {{ ref('fct_messages') }} (message_id)
);
