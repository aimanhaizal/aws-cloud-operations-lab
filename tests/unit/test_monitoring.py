
from unittest.mock import Mock, patch

import requests

from cloudops_lab.monitoring import check_http_service


@patch("cloudops_lab.monitoring.requests.get")
def test_http_service_reports_healthy_response(mock_get):
    mock_get.return_value = Mock(status_code=200)

    result = check_http_service(
        "Example API",
        "https://example.test/health",
    )

    assert result["name"] == "Example API"
    assert result["status"] == "healthy"
    assert result["status_code"] == 200
    assert result["error"] is None
    mock_get.assert_called_once_with(
        "https://example.test/health",
        timeout=3.0,
    )


@patch("cloudops_lab.monitoring.requests.get")
def test_http_service_reports_http_error(mock_get):
    mock_get.return_value = Mock(status_code=503)

    result = check_http_service(
        "Example API",
        "https://example.test/health",
    )

    assert result["status"] == "unhealthy"
    assert result["status_code"] == 503


@patch("cloudops_lab.monitoring.requests.get")
def test_http_service_handles_connection_failure(mock_get):
    mock_get.side_effect = requests.ConnectionError()

    result = check_http_service(
        "Example API",
        "https://example.test/health",
    )

    assert result["status"] == "unhealthy"
    assert result["status_code"] is None
    assert result["error"] == "ConnectionError"
