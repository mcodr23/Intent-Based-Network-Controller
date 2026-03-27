def _admin_headers(client):
    login = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_end_to_end_flow(client):
    headers = _admin_headers(client)

    discovery = client.post("/api/discovery/start", json={"subnet": "10.0.0.0/29"}, headers=headers)
    assert discovery.status_code == 200, discovery.text
    assert discovery.json()["discovered"] >= 1

    devices = client.get("/api/devices", headers=headers)
    assert devices.status_code == 200, devices.text
    assert len(devices.json()) >= 1

    policy_payload = {
        "name": "Test Isolation Policy",
        "description": "deny guest to corporate",
        "source_group": "guest",
        "destination_group": "corporate",
        "action": "deny",
        "scope": "campus",
        "parameters": {"vlan_id": 30},
    }
    policy = client.post("/api/intent", json=policy_payload, headers=headers)
    assert policy.status_code == 200, policy.text
    policy_id = policy.json()["id"]

    deploy = client.post(f"/api/deploy/{policy_id}", json={}, headers=headers)
    assert deploy.status_code == 200, deploy.text
    deployment_id = deploy.json()["deployment"]["id"]

    deployment_info = client.get(f"/api/deployments/{deployment_id}", headers=headers)
    assert deployment_info.status_code == 200, deployment_info.text

    deployment_logs = client.get(f"/api/deployments/{deployment_id}/logs", headers=headers)
    assert deployment_logs.status_code == 200, deployment_logs.text
    assert len(deployment_logs.json()) >= 1

    compliance = client.get("/api/compliance", headers=headers)
    assert compliance.status_code == 200, compliance.text

    telemetry = client.get("/api/telemetry", headers=headers)
    assert telemetry.status_code == 200, telemetry.text
    assert len(telemetry.json()) >= 1


def test_viewer_rbac(client):
    register = client.post(
        "/api/register",
        json={
            "username": "viewer_user",
            "email": "viewer@example.com",
            "password": "viewer123",
            "role": "Viewer",
        },
    )
    assert register.status_code == 200, register.text

    login = client.post("/api/login", json={"username": "viewer_user", "password": "viewer123"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    denied = client.post("/api/discovery/start", json={}, headers=headers)
    assert denied.status_code == 403

    allowed = client.get("/api/devices", headers=headers)
    assert allowed.status_code == 200
