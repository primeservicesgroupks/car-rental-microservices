"""Verify JWT signature, expiration, identity claims, and missing tokens."""

def test_missing_token_rejected(client, vehicle_payload):
    assert client.post("/vehicles", json=vehicle_payload).status_code == 401

def test_invalid_signature_rejected(client, auth_header, vehicle_payload):
    response = client.post("/vehicles", json=vehicle_payload, headers=auth_header(secret="wrong-key-for-test-signature-validation-123456"))
    assert response.status_code == 401

def test_expired_token_rejected(client, auth_header, vehicle_payload):
    assert client.post("/vehicles", json=vehicle_payload, headers=auth_header(expired=True)).status_code == 401

def test_invalid_role_rejected(client, auth_header, vehicle_payload):
    assert client.post("/vehicles", json=vehicle_payload, headers=auth_header(role="SUPERUSER")).status_code == 401
