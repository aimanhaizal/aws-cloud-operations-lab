
from cloudops_lab import create_app


def test_demo_service_starts_healthy():
    app = create_app()
    response = app.test_client().get("/demo/payment-health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_demo_service_can_simulate_failure_and_recover():
    app = create_app()
    client = app.test_client()

    failure = client.post("/demo/simulate-failure")
    assert failure.status_code == 200

    failed_health = client.get("/demo/payment-health")
    assert failed_health.status_code == 503
    assert failed_health.get_json()["status"] == "unhealthy"

    restore = client.post("/demo/restore")
    assert restore.status_code == 200

    recovered_health = client.get("/demo/payment-health")
    assert recovered_health.status_code == 200
    assert recovered_health.get_json()["status"] == "healthy"
