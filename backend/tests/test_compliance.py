"""Tests for ISO 19650 compliance and PDF export endpoints."""


def test_iso_compliance(client, auth_headers, project_id):
    res = client.get(f"/api/projects/{project_id}/iso-compliance", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "overall_score" in data
    assert "parts" in data
    assert "recommendations" in data
    assert "total_checks" in data
    assert "pass_count" in data
    # All parts present
    assert "iso_19650_1" in data["parts"]
    assert "iso_19650_2" in data["parts"]
    assert "iso_19650_3" in data["parts"]
    assert "iso_19650_5" in data["parts"]


def test_iso_compliance_not_found(client, auth_headers):
    res = client.get("/api/projects/99999/iso-compliance", headers=auth_headers)
    assert res.status_code == 200  # Returns error dict, not 404
    data = res.json()
    assert "error" in data


def test_export_compliance_pdf(client, auth_headers, project_id):
    res = client.get(
        f"/api/projects/{project_id}/export-compliance-pdf",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000  # PDF should be > 1KB
    # Check PDF magic bytes
    assert res.content[:4] == b"%PDF"


def test_export_compliance_pdf_not_found(client, auth_headers):
    res = client.get(
        "/api/projects/99999/export-compliance-pdf",
        headers=auth_headers,
    )
    assert res.status_code == 404
