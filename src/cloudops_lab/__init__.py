# import os
from cloudops_lab.config import MONITORED_SERVICES

from flask import Flask, jsonify, render_template

from cloudops_lab.monitoring import check_http_service


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

    # monitored_services = [
    #     {
    #         "name": "CloudOps Dashboard",
    #         "url": os.environ.get(
    #             "CLOUDOPS_HEALTH_URL",
    #             "http://127.0.0.1:8001/health",
    #         ),
    #     },
    # ]



    @app.get("/")
    def index():
        # service_health = [
        #     check_http_service(service["name"], service["url"])
        #     for service in monitored_services
        # ]

        service_health = [
            check_http_service(service["name"], service["url"])
            for service in MONITORED_SERVICES
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
