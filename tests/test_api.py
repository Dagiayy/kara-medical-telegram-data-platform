from fastapi.testclient import TestClient

import api.crud as crud
from api.database import get_db
from api.main import app


def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_health_reports_status_even_without_a_live_db():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in {"ok", "degraded"}


def test_top_products_returns_mocked_rows(monkeypatch):
    monkeypatch.setattr(
        crud,
        "get_top_products",
        lambda conn, limit, offset: [{"product_name": "Amoxicillin", "category": "antibiotic", "mention_count": 5}],
    )
    resp = client.get("/api/reports/top-products")
    assert resp.status_code == 200
    assert resp.json()[0]["product_name"] == "Amoxicillin"


def test_search_messages_requires_min_length():
    resp = client.get("/api/search/messages", params={"query": "a"})
    assert resp.status_code == 422


def test_channel_activity_404_for_unknown_channel(monkeypatch):
    monkeypatch.setattr(crud, "channel_exists", lambda conn, name: False)
    resp = client.get("/api/channels/doesnotexist/activity")
    assert resp.status_code == 404


def test_channel_activity_200_for_known_channel(monkeypatch):
    monkeypatch.setattr(crud, "channel_exists", lambda conn, name: True)
    monkeypatch.setattr(
        crud, "get_channel_activity", lambda conn, name, limit, offset: [{"date": "2025-07-13", "message_count": 3}]
    )
    resp = client.get("/api/channels/tikvahpharma/activity")
    assert resp.status_code == 200
    assert resp.json()[0]["message_count"] == 3


def test_pagination_limit_is_bounded():
    resp = client.get("/api/reports/top-products", params={"limit": 100000})
    assert resp.status_code == 422
