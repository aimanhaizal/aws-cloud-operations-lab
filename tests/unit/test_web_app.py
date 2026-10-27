
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
