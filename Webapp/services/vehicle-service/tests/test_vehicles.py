"""Test vehicle CRUD, persistence, filtering, and validation."""

def test_public_list_starts_empty(client):
    response = client.get("/vehicles")
    assert response.status_code == 200
    assert response.json() == []

def test_owner_creates_and_reads_vehicle(client, auth_header, vehicle_payload):
    created = client.post("/vehicles", json=vehicle_payload, headers=auth_header())
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["owner_id"] == 10
    assert body["daily_rate"] == "45.00"
    assert body["is_available"] is True
    assert client.get("/vehicles/" + str(body["id"])).status_code == 200
    assert len(client.get("/vehicles").json()) == 1

def test_owner_can_update_and_toggle_availability(client, auth_header, vehicle_payload):
    vehicle_id = client.post("/vehicles", json=vehicle_payload, headers=auth_header()).json()["id"]
    updated = client.put(f"/vehicles/{vehicle_id}", json={"daily_rate": "50.00"}, headers=auth_header())
    assert updated.status_code == 200
    assert updated.json()["daily_rate"] == "50.00"
    changed = client.patch(f"/vehicles/{vehicle_id}/availability", json={"is_available": False}, headers=auth_header())
    assert changed.status_code == 200
    assert changed.json()["is_available"] is False
    assert client.get("/vehicles?available_only=true").json() == []

def test_validation_and_unknown_vehicle(client, auth_header, vehicle_payload):
    assert client.get("/vehicles/99999").status_code == 404
    assert client.post("/vehicles", json={**vehicle_payload, "daily_rate": "-1"}, headers=auth_header()).status_code == 422
    assert client.post("/vehicles", json={**vehicle_payload, "owner_id": 999}, headers=auth_header()).status_code == 422
    assert client.get("/vehicles?limit=1000").status_code == 422

def test_my_vehicles_only_returns_own(client, auth_header, vehicle_payload):
    client.post("/vehicles", json=vehicle_payload, headers=auth_header(user_id=10))
    client.post("/vehicles", json=vehicle_payload, headers=auth_header(user_id=11))
    response = client.get("/vehicles/mine", headers=auth_header(user_id=10))
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["owner_id"] == 10
