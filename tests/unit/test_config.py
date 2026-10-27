
from cloudops_lab.config import MONITORED_SERVICES


def test_monitoring_configuration_contains_two_services():
    names = [service["name"] for service in MONITORED_SERVICES]

    assert "CloudOps Dashboard" in names
    assert "Demo Payment API" in names


def test_monitoring_configuration_has_urls():
    for service in MONITORED_SERVICES:
        assert service["url"].startswith("http://")
