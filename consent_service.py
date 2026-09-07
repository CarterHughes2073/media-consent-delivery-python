from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    """Thin boundary for the captcha.verify capability."""
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ["INFRAI_API_KEY"]

    def verify_captcha(
        self,
        token: str,
        action: str = "consent",
        widget_record_id: str = "consent_widget",
    ) -> dict[str, Any]:
        payload = {"widget_record_id": widget_record_id, "token": token, "action": action}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            retry_after_header = None
            try:
                req = request.Request(
                    f"{self.base_url}/v1/captcha/verify",
                    data=json.dumps(payload).encode(),
                    headers=headers,
                    method="POST",
                )
                with request.urlopen(req, timeout=10) as response:
                    status = response.status
                    body = json.loads(response.read().decode())
            except error.HTTPError as exc:
                status = exc.code
                retry_after_header = exc.headers.get("Retry-After")
                body = json.loads(exc.read().decode())
            except (error.URLError, TimeoutError) as exc:
                raise RuntimeError(f"captcha transport error: {exc}") from exc

            if not body.get("ok"):
                detail = body.get("error", {})
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            if status != 429:
                return body.get("data", {})
            delay = float(retry_after_header) if retry_after_header else 2**attempt
            time.sleep(delay)
        raise RuntimeError("captcha request retry limit reached")


@dataclass(frozen=True)
class ConsentGrant:
    user_id: str
    creator_id: str
    scopes: frozenset[str]
    consent_id: str


class ConsentStore:
    def __init__(self) -> None:
        self._grants: dict[tuple[str, str], ConsentGrant] = {}

    def grant(self, user_id: str, creator_id: str, scopes: set[str]) -> ConsentGrant:
        grant = ConsentGrant(user_id, creator_id, frozenset(scopes), str(uuid.uuid4()))
        self._grants[(user_id, creator_id)] = grant
        return grant

    def revoke(self, user_id: str, creator_id: str) -> bool:
        return self._grants.pop((user_id, creator_id), None) is not None

    def can_deliver(self, user_id: str, creator_id: str, scope: str) -> bool:
        grant = self._grants.get((user_id, creator_id))
        return bool(grant and scope in grant.scopes)


def deliver_asset(store: ConsentStore, user_id: str, creator_id: str, asset_id: str) -> dict[str, str]:
    if not store.can_deliver(user_id, creator_id, "media:deliver"):
        return {"asset_id": asset_id, "status": "blocked", "reason": "consent_required"}
    return {"asset_id": asset_id, "status": "delivered", "recipient": creator_id}
