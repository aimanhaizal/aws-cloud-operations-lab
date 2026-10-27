
import os


MONITORED_SERVICES = [
    {
        "name": "CloudOps Dashboard",
        "url": os.environ.get(
            "CLOUDOPS_HEALTH_URL",
            "http://127.0.0.1:8000/health",
        ),
    },
    {
        "name": "Demo Payment API",
        "url": os.environ.get(
            "DEMO_PAYMENT_API_URL",
            "http://127.0.0.1:8000/demo/payment-health",
        ),
    },
]
