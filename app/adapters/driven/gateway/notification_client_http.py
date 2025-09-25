import json
import time
import urllib.request
import os

from dataclasses import dataclass
from typing import Optional
from app.domain.ports.notification import NotificationPort, Status


@dataclass
class HttpNotificationClient(NotificationPort):
    """
    Cliente HTTP para o notification-service.
    POST { user_id, job_id, status, video_url?, error_message? } em /notify.
    """

    def __init__(self):
        self.base_url = os.getenv("NOTIFIER_URL")
        self.notifier_retry = int(os.getenv("NOTIFIER_RETRY"))
        self.notifier_timeout = os.getenv("NOTIFIER_TIMEOUT")

    def notify(
        self,
        *,
        user_id: id,
        job_id: str,
        status: Status,
        video_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        payload = {
            "id": user_id,
            "job_id": job_id,
            "status": status,
        }
        if video_url:
            payload["video_url"] = video_url
        if error_message:
            payload["error_message"] = error_message

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=f"{self.base_url}/notify",
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        last_exc: Exception | None = None
        for attempt in range(1, self.notifier_retry + 2):
            try:
                with urllib.request.urlopen(req, timeout=self.notifier_timeout) as r:
                    # sucesso (200-299). não precisamos do body.
                    _ = r.read()
                    return
            except Exception as e:
                last_exc = e
                time.sleep(min(2 ** (attempt - 1), 4))

        # logger.warning(f"[notify] falha ao notificar job={job_id}: {last_exc}")
        return
