
from flask import Flask, jsonify, render_template


def create_app():
    app = Flask(__name__)

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
        return render_template(
            "index.html",
            equipment=equipment,
            requests=requests,
        )

    @app.get("/health")
    def health():
        return jsonify(status="healthy"), 200

    return app
