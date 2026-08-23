from app.scraper.load_raw_to_pg import parse_message_record, upsert_images


def test_parse_message_record_valid():
    raw = {
        "id": 172432,
        "date": "2025-07-13 08:14:17+00:00",
        "sender_id": -1001353257880,
        "text": "Amoxicillin 500mg in stock",
        "media_type": None,
        "media_url": None,
        "media_size_kb": None,
        "width": None,
        "height": None,
    }
    record = parse_message_record(raw, channel="tikvahpharma")
    assert record is not None
    channel, msg_id, sent_at, sender_id, text, *_rest = record
    assert channel == "tikvahpharma"
    assert msg_id == 172432
    assert sender_id == "-1001353257880"
    assert text == "Amoxicillin 500mg in stock"
    assert sent_at is not None


def test_parse_message_record_missing_id_is_skipped():
    raw = {"date": "2025-07-13 08:14:17+00:00", "text": "no id here"}
    assert parse_message_record(raw, channel="x") is None


def test_parse_message_record_bad_date_is_skipped():
    raw = {"id": 1, "date": "not-a-date", "text": "hi"}
    assert parse_message_record(raw, channel="x") is None


def test_upsert_images_only_includes_photo_messages():
    records = [
        ("chan", 1, None, "s1", "text only", None, None, None, None, None),
        ("chan", 2, None, "s1", "caption", "photo", "data_lake/raw/media/x.jpg", 10.0, 640, 640),
    ]

    captured = {}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def execute(self, *_args, **_kwargs):
            pass

    class FakeConn:
        def cursor(self):
            return FakeCursor()

    import app.scraper.load_raw_to_pg as mod

    def fake_execute_values(_cur, _sql, rows):
        captured["rows"] = rows

    orig = mod.execute_values
    mod.execute_values = fake_execute_values
    try:
        count = upsert_images(FakeConn(), records)
    finally:
        mod.execute_values = orig

    assert count == 1
    assert captured["rows"] == [("chan", 2, "data_lake/raw/media/x.jpg")]
