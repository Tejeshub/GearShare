import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.contact import ContactMessage


def test_submit_contact_message(client: TestClient, db_session: Session):
    payload = {
        "name": "Alex Morgan",
        "email": "alex@example.com",
        "message": "I am shooting a commercial next month and need camera packages.",
    }
    response = client.post("/api/v1/contact", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alex Morgan"
    assert data["email"] == "alex@example.com"
    assert "id" in data
    assert "created_at" in data

    # Verify saved in database
    saved = db_session.query(ContactMessage).filter(ContactMessage.email == "alex@example.com").first()
    assert saved is not None
    assert saved.message == payload["message"]


def test_submit_contact_message_validation_failure(client: TestClient):
    payload = {
        "name": "",
        "email": "not-an-email",
        "message": "",
    }
    response = client.post("/api/v1/contact", json=payload)
    assert response.status_code == 422
