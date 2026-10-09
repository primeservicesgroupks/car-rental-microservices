"""Verify role checks, owner boundaries, and ADMIN overrides."""

def test_renter_cannot_create(client, auth_header, vehicle_payload):
    response = client.post("/vehicles", json=vehicle_payload, headers=auth_header(role="RENTER"))
    assert response.status_code == 403

def test_other_owner_cannot_modify(client, auth_header, vehicle_payload):
    vehicle_id = client.post("/vehicles", json=vehicle_payload, headers=auth_header(user_id=10)).json()["id"]
    response = client.put(f"/vehicles/{vehicle_id}", json={"city": "Wichita"}, headers=auth_header(user_id=11))
    assert response.status_code == 403
    response = client.patch(f"/vehicles/{vehicle_id}/availability", json={"is_available": False}, headers=auth_header(user_id=11))
    assert response.status_code == 403

def test_admin_can_modify_any_vehicle(client, auth_header, vehicle_payload):
    vehicle_id = client.post("/vehicles", json=vehicle_payload, headers=auth_header(user_id=10)).json()["id"]
    response = client.put(f"/vehicles/{vehicle_id}", json={"city": "Wichita"}, headers=auth_header(user_id=99, role="ADMIN"))
    assert response.status_code == 200
    assert response.json()["city"] == "Wichita"
    assert response.json()["owner_id"] == 10

def test_renter_cannot_edit_even_own_listing(client, auth_header, vehicle_payload):
    vehicle_id = client.post("/vehicles", json=vehicle_payload, headers=auth_header(user_id=10)).json()["id"]
    response = client.put(f"/vehicles/{vehicle_id}", json={"city": "Wichita"}, headers=auth_header(user_id=10, role="RENTER"))
    assert response.status_code == 403

def test_owner_cannot_change_owner_id(client, auth_header, vehicle_payload):
    vehicle_id = client.post("/vehicles", json=vehicle_payload, headers=auth_header()).json()["id"]
    response = client.put(f"/vehicles/{vehicle_id}", json={"owner_id": 999}, headers=auth_header())
    assert response.status_code == 422
