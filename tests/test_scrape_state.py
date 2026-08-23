import app.scraper.scrape_telegram as scraper


def test_state_roundtrip(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(scraper, "STATE_FILE", str(state_file))

    assert scraper.load_state() == {}

    scraper.save_state({"tikvahpharma": 172432})
    assert scraper.load_state() == {"tikvahpharma": 172432}


def test_load_state_handles_corrupt_file(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    state_file.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(scraper, "STATE_FILE", str(state_file))

    assert scraper.load_state() == {}
