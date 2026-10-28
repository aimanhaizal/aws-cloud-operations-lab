# import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template


def create_app():
    app = Flask(__name__)
    app.config["DEMO_PAYMENT_FAILED"] = False

    equipment = [
        {
            "id": 1,
            "name": "Production Server A",
            "location": "Data Centre",
            "status": "Operational",
        },
        {
            "id": 2,
            "name": "Network Switch B",
            "location": "Network Room",
            "status": "Maintenance due",
        },
        {
            "id": 3,
            "name": "Backup Storage C",
            "location": "Data Centre",
            "status": "Operational",
        },
    ]

    requests = [
        {
            "id": 1001,
            "equipment": "Network Switch B",
            "priority": "High",
            "status": "In Progress",
        },
        {
            "id": 1002,
            "equipment": "Backup Storage C",
            "priority": "Medium",
            "status": "Scheduled",
        },
        {
            "id": 1003,
            "equipment": "Production Server A",
            "priority": "Low",
            "status": "Open",
        },
    ]

    @app.get("/")
    def index():
        checked_at = datetime.now(timezone.utc).isoformat()
        payment_failed = app.config["DEMO_PAYMENT_FAILED"]

        service_health = [
            {
                "name": "CloudOps Dashboard",
                "status": "healthy",
                "status_code": 200,
                "response_time_ms": None,
                "checked_at": checked_at,
                "error": None,
            },
            {
                "name": "Demo Payment API",
                "status": "unhealthy" if payment_failed else "healthy",
                "status_code": 503 if payment_failed else 200,
                "response_time_ms": None,
                "checked_at": checked_at,
                "error": None,
            },
        ]

        return render_template(
            "index.html",
            equipment=equipment,
            requests=requests,
            service_health=service_health,
        )

    @app.get("/health")
    def health():
        return jsonify(status="healthy"), 200

    @app.get("/demo/payment-health")
    def demo_payment_health():
        if app.config["DEMO_PAYMENT_FAILED"]:
            return jsonify(status="unhealthy", simulated=True), 503

        return jsonify(status="healthy", simulated=True), 200

    @app.post("/demo/simulate-failure")
    def simulate_failure():
        app.config["DEMO_PAYMENT_FAILED"] = True
        return jsonify(status="unhealthy", simulated=True), 200

    @app.post("/demo/restore")
    def restore_service():
        app.config["DEMO_PAYMENT_FAILED"] = False
        return jsonify(status="healthy", simulated=True), 200

    return app
