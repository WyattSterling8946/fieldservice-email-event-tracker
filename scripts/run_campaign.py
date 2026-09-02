"""Run one dispatch update and inspect its delivery events."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.fieldservice_mail import InfraiClient, WorkOrder, follow_up_after_events, send_dispatch_update


def main() -> None:
    order = WorkOrder(
        order_id="WO-1042",
        technician="Mina Chen",
        dispatch_status="on route",
        photo_names=("meter.jpg", "panel.jpg"),
        technician_email=os.environ.get("FIELD_TECH_EMAIL", "technician@example.com"),
    )
    client = InfraiClient()
    message_id = send_dispatch_update(client, order)
    details = client.email_get(message_id)
    followed_up = follow_up_after_events(client, order, message_id)
    print({"message_id": message_id, "email": details, "follow_up_sent": followed_up})


if __name__ == "__main__":
    main()
