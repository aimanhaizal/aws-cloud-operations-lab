
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

def test_dashboard_renders_service_health_without_http_probes():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Service health" in response.data
    assert b"CloudOps Dashboard" in response.data
    assert b"Demo Payment API" in response.data
    assert response.data.count(b"HEALTHY") == 2
    assert b"12.5 ms" not in response.data


def test_dashboard_health_reflects_simulated_payment_failure():
    app = create_app()
    client = app.test_client()

    client.post("/demo/simulate-failure")
    response = client.get("/")

    assert response.status_code == 200
    assert b"CloudOps Dashboard" in response.data
    assert b"Demo Payment API" in response.data
    assert b"UNHEALTHY" in response.data

    client.post("/demo/restore")
    response = client.get("/")

    assert response.status_code == 200
    assert response.data.count(b"HEALTHY") == 2



def test_dashboard_includes_failure_simulation_controls():
    app = create_app()
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Simulate failure" in response.data
    assert b"Restore service" in response.data
    assert b"/demo/simulate-failure" in response.data
    assert b"/demo/restore" in response.data