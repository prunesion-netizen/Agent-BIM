"""Tests for notification endpoints."""


def test_notification_count_empty(client, auth_headers):
    res = client.get("/api/notifications/count", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["unread_count"] == 0


def test_list_notifications_empty(client, auth_headers):
    res = client.get("/api/notifications", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_notification_lifecycle(client, auth_headers, project_id, db_session):
    """Create notification via service, then test list/read/read-all."""
    # Get user id from /me
    me = client.get("/api/auth/me", headers=auth_headers).json()
    user_id = me["id"]

    # Create notification directly via service
    from app.services.notification_service import create_notification
    create_notification(
        db_session, user_id,
        title="Test notificare",
        message="Aceasta este o notificare de test.",
        category="info",
        project_id=project_id,
    )

    # Count should be 1
    res = client.get("/api/notifications/count", headers=auth_headers)
    assert res.json()["unread_count"] == 1

    # List should have 1 item
    res = client.get("/api/notifications", headers=auth_headers)
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test notificare"
    assert data[0]["is_read"] is False
    notif_id = data[0]["id"]

    # Mark as read
    res = client.post(f"/api/notifications/{notif_id}/read", headers=auth_headers)
    assert res.status_code == 200

    # Count should be 0
    res = client.get("/api/notifications/count", headers=auth_headers)
    assert res.json()["unread_count"] == 0


def test_mark_all_read(client, auth_headers, project_id, db_session):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    user_id = me["id"]

    from app.services.notification_service import create_notification
    for i in range(3):
        create_notification(
            db_session, user_id,
            title=f"Notif {i}",
            message=f"Message {i}",
            category="info",
        )

    res = client.get("/api/notifications/count", headers=auth_headers)
    assert res.json()["unread_count"] == 3

    res = client.post("/api/notifications/read-all", headers=auth_headers)
    assert res.status_code == 200

    res = client.get("/api/notifications/count", headers=auth_headers)
    assert res.json()["unread_count"] == 0


def test_mark_nonexistent_notification(client, auth_headers):
    res = client.post("/api/notifications/99999/read", headers=auth_headers)
    assert res.status_code == 404


def test_unread_only_filter(client, auth_headers, db_session):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    user_id = me["id"]

    from app.services.notification_service import create_notification
    n1 = create_notification(db_session, user_id, title="N1", message="M1", category="info")
    create_notification(db_session, user_id, title="N2", message="M2", category="bep")

    # Mark first as read
    client.post(f"/api/notifications/{n1.id}/read", headers=auth_headers)

    # Unread only should return 1
    res = client.get("/api/notifications?unread_only=true", headers=auth_headers)
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "N2"
