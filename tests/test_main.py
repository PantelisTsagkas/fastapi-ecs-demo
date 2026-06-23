from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "fastapi-ecs-demo" in response.text


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_and_get_item() -> None:
    create_response = client.post("/items", json={"name": "test item"})
    assert create_response.status_code == 201
    item_id = create_response.json()["id"]

    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "test item"


def test_get_missing_item_returns_404() -> None:
    response = client.get("/items/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
