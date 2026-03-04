"""Tests for ISO 19650 module endpoints (EIR, TIDP, RACI, LOIN, etc.)."""


def test_eir_empty(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/eir", headers=auth_headers)
    assert res.status_code in (200, 404)


def test_deliverables_generate(client, auth_headers, project_id):
    """Deliverables endpoint is POST (generate), not GET list."""
    res = client.post(f"/api/projects/{project_id}/deliverables", headers=auth_headers)
    # Without context, may return 200 with empty or error
    assert res.status_code in (200, 400, 404, 422)


def test_raci_empty(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/raci", headers=auth_headers)
    assert res.status_code == 200


def test_loin_empty(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/loin", headers=auth_headers)
    assert res.status_code == 200


def test_handover_empty(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/handover", headers=auth_headers)
    assert res.status_code == 200


def test_clashes_empty(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/clashes", headers=auth_headers)
    assert res.status_code == 200


def test_kpis(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/kpis", headers=auth_headers)
    assert res.status_code == 200


def test_security_empty(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/security-classification", headers=auth_headers)
    assert res.status_code in (200, 404)


def test_cobie_validations_empty(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/cobie-validations", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == [] or isinstance(res.json(), list)


def test_healthcheck(client):
    """Test global healthcheck endpoint."""
    res = client.get("/healthcheck")
    assert res.status_code == 200
