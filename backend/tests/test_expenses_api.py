from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Expense, IdempotencyRecord

client = TestClient(app)


def setup_function():
    with SessionLocal() as db:
        db.query(IdempotencyRecord).delete()
        db.query(Expense).delete()
        db.commit()


def test_create_is_idempotent_with_key():
    payload = {
        "amount": "120.50",
        "category": "Food",
        "description": "Lunch",
        "date": "2026-04-20",
    }
    headers = {"Idempotency-Key": "same-request-key"}

    first = client.post("/expenses", json=payload, headers=headers)
    second = client.post("/expenses", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_list_supports_filter_and_date_desc_sort():
    items = [
        {
            "amount": "50.00",
            "category": "Travel",
            "description": "Cab",
            "date": "2026-04-19",
        },
        {
            "amount": "90.00",
            "category": "Food",
            "description": "Dinner",
            "date": "2026-04-20",
        },
    ]
    for item in items:
        assert client.post("/expenses", json=item).status_code in (200, 201)

    filtered = client.get("/expenses", params={"category": "Food", "sort": "date_desc"})
    assert filtered.status_code == 200
    payload = filtered.json()
    assert len(payload) == 1
    assert payload[0]["category"] == "Food"
    assert payload[0]["date"] == "2026-04-20"
