"""Tests for project CRUD endpoints."""


def test_create_project(client, auth_headers):
    res = client.post("/api/projects", json={
        "name": "New Project",
        "code": "NP01",
        "client_name": "Client A",
        "project_type": "building",
    }, headers=auth_headers)
    assert res.status_code == 200 or res.status_code == 201
    data = res.json()
    assert data["name"] == "New Project"
    assert data["code"] == "NP01"
    assert data["status"] == "new"


def test_create_project_unauthenticated(client):
    res = client.post("/api/projects", json={
        "name": "X", "code": "X01", "client_name": "C",
    })
    assert res.status_code in (401, 403)


def test_list_projects(client, auth_headers, project_id):
    res = client.get("/api/projects", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(p["id"] == project_id for p in data)


def test_get_project(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["project"]["id"] == project_id
    assert data["project"]["code"] == "TST01"


def test_get_project_not_found(client, auth_headers):
    res = client.get("/api/projects/99999", headers=auth_headers)
    assert res.status_code == 404


def test_update_project(client, auth_headers, project_id):
    res = client.patch(f"/api/projects/{project_id}", json={
        "name": "Updated Name",
    }, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Name"


def test_delete_project(client, auth_headers, project_id):
    res = client.delete(f"/api/projects/{project_id}", headers=auth_headers)
    assert res.status_code == 204
    # Verify deleted
    res2 = client.get(f"/api/projects/{project_id}", headers=auth_headers)
    assert res2.status_code == 404


def test_projects_overview(client, auth_headers, project_id):
    res = client.get("/api/projects/overview", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    overview = data[0]
    assert "health_score" in overview
    assert "has_bep" in overview
    assert "status" in overview
