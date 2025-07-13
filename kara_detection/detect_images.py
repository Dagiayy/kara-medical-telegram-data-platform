import os
from ultralytics import YOLO
import psycopg2

# --- Config ---

# Path where images are stored
IMAGES_FOLDER = 'path/to/images'

# Database connection params
DB_PARAMS = {
    'host': 'localhost',
    'dbname': 'kara_db',
    'user': 'karauser',
    'password': 'karapass',
    'port': 5432,
}

# YOLOv8 model
MODEL = YOLO('yolov8n.pt')  # you can choose different pretrained weights


# --- Functions ---

def get_unprocessed_images(conn):
    """
    Query DB to get list of images that have not yet been processed.
    This assumes you have a table with images linked to messages, and
    a way to mark which images are processed.
    Modify based on your schema.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT image_id, message_id, image_path
            FROM images_table
            WHERE processed = FALSE;
        """)
        return cur.fetchall()

def save_detections(conn, message_id, detections):
    """
    Insert detections into fct_image_detections table.
    detections is a list of dicts with keys: class_name, confidence_score
    """
    with conn.cursor() as cur:
        for det in detections:
            cur.execute("""
                INSERT INTO fct_image_detections (message_id, detected_object_class, confidence_score)
                VALUES (%s, %s, %s)
            """, (message_id, det['class_name'], det['confidence_score']))
    conn.commit()

def mark_image_processed(conn, image_id):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE images_table SET processed = TRUE WHERE image_id = %s
        """, (image_id,))
    conn.commit()

def detect_objects(image_path):
    results = MODEL(image_path)
    detections = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            cls_name = MODEL.names[cls_id]
            detections.append({
                'class_name': cls_name,
                'confidence_score': conf
            })
    return detections


def main():
    conn = psycopg2.connect(**DB_PARAMS)
    images = get_unprocessed_images(conn)
    print(f"Found {len(images)} images to process.")

    for image_id, message_id, image_path in images:
        print(f"Processing image {image_path} for message {message_id}")
        detections = detect_objects(image_path)
        print(f"Detected objects: {detections}")
        save_detections(conn, message_id, detections)
        mark_image_processed(conn, image_id)

    conn.close()


if __name__ == "__main__":
    main()
