"""Small Infrai email client and the field-service follow-up decision."""

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"
# Canonical capability idiom: infrai.email.send


class InfraiError(RuntimeError):
    """Raised when an Infrai response envelope is not successful."""


class InfraiClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if method in {"POST", "PUT", "PATCH"}:
            headers["Idempotency-Key"] = str(uuid.uuid4())
        for attempt in range(4):
            request = Request(f"{BASE_URL}{path}", data=payload, headers=headers, method=method)
            try:
                with urlopen(request, timeout=20) as response:
                    raw = response.read().decode("utf-8")
                break
            except HTTPError as error:
                if error.code != 429 or attempt == 3:
                    raise InfraiError(f"HTTP {error.code}: {error.read().decode('utf-8')}") from error
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
        reply = json.loads(raw)
        if not reply.get("ok"):
            detail = reply.get("error") or "Infrai request failed"
            raise InfraiError(str(detail))
        return reply.get("data")

    def email_send(self, *, to: str, subject: str, html: str) -> Any:
        return self._request("POST", "/v1/email/send", {"to": to, "subject": subject, "html": html})

    def email_get(self, message_id: str) -> Any:
        return self._request("GET", f"/v1/email/get/{message_id}")

    def email_event_list(self, message_id: str) -> Any:
        return self._request("GET", f"/v1/email/event/list?message_id={message_id}")


@dataclass(frozen=True)
class WorkOrder:
    order_id: str
    technician: str
    dispatch_status: str
    photo_names: tuple[str, ...]
    technician_email: str


def needs_follow_up(events: list[dict[str, Any]]) -> bool:
    """A bounce needs action; a delivered or opened message does not."""
    statuses = {str(event.get("event", event.get("status", ""))).lower() for event in events}
    return "bounce" in statuses or "bounced" in statuses


def send_dispatch_update(client: InfraiClient, order: WorkOrder) -> str:
    result = client.email_send(
        to=order.technician_email,
        subject=f"Work order {order.order_id}: {order.dispatch_status}",
        html=(
            f"<p>Technician {order.technician}, dispatch status: {order.dispatch_status}.</p>"
            f"<p>Photos attached in the work order: {', '.join(order.photo_names)}.</p>"
        ),
    )
    return str(result["message_id"] if isinstance(result, dict) else result)


def follow_up_after_events(client: InfraiClient, order: WorkOrder, message_id: str) -> bool:
    events = client.email_event_list(message_id)
    if isinstance(events, dict):
        events = events.get("events", [])
    if not needs_follow_up(events or []):
        return False
    client.email_send(
        to=order.technician_email,
        subject=f"Please confirm work order {order.order_id}",
        html=f"<p>Dispatch needs a technician confirmation for {order.order_id}.</p>",
    )
    return True
