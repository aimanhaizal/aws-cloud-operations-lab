
from cloudops_lab import create_app


def test_health_endpoint_returns_healthy():
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


def test_dashboard_renders_equipment_and_requests():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"CloudOps Equipment Maintenance Hub" in response.data
    assert b"Production Server A" in response.data
    assert b"Network Switch B" in response.data
    assert b"Maintenance requests" in response.data


def test_dashboard_renders_service_health():
    from unittest.mock import patch

    app = create_app()

    mock_health = {
        "name": "CloudOps Dashboard",
        "url": "http://127.0.0.1:8000/health",
        "status": "healthy",
        "status_code": 200,
        "response_time_ms": 12.5,
        "checked_at": "2026-10-27T06:00:00+00:00",
        "error": None,
    }

    with patch(
        "cloudops_lab.check_http_service",
        return_value=mock_health,
    ):
        response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Service health" in response.data
    assert b"CloudOps Dashboard" in response.data
    assert b"HEALTHY" in response.data
    assert b"12.5 ms" in response.data


def test_dashboard_includes_failure_simulation_controls():
    app = create_app()
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Simulate failure" in response.data
    assert b"Restore service" in response.data
    assert b"/demo/simulate-failure" in response.data
    assert b"/demo/restore" in response.data