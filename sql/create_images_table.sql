CREATE TABLE images_table (
    image_id SERIAL PRIMARY KEY,
    message_id INT NOT NULL,
    image_path TEXT NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (message_id) REFERENCES fct_messages(message_id)
);
