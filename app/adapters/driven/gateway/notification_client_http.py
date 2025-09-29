import json
import time
import urllib.request
import urllib.error
import os
import logging
from dataclasses import dataclass
from typing import Optional, Any
from app.domain.ports.notification import NotificationPort, Status

logger = logging.getLogger(__name__)

@dataclass
class HttpNotificationClient(NotificationPort):
    """
    Cliente HTTP para o notification-service.
    POST { user_id, job_id, status, video_url?, error_message? } em /notify.
    """

    def __init__(self):
        self.base_url = os.getenv("NOTIFIER_URL")
        self.notifier_retry = int(os.getenv("NOTIFIER_RETRY", "3"))
        # urllib espera float/segundos
        self.notifier_timeout = float(os.getenv("NOTIFIER_TIMEOUT", "5"))

    def notify(
        self,
        *,
        user_id: Any,            # tipagem flexível; ajuste para int|str se preferir
        job_id: str,
        status: Status,
        video_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        payload: dict[str, Any] = {
            "user_id": user_id,
            "job_id": job_id,
            "status": getattr(status, "value", str(status)),
        }
        if video_url:
            payload["video_url"] = video_url
        if error_message:
            payload["error_message"] = error_message

        data = json.dumps(payload).encode("utf-8")
        url = f"{self.base_url}/notify"

        print(f"[notify] URL: {url}")
        print(f"[notify] Payload: {payload}")

        req = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        last_exc: Exception | None = None

        # total de tentativas = retries + 1
        for attempt in range(1, self.notifier_retry + 2):
            print(f"[notify] Tentativa {attempt}/{self.notifier_retry + 1}...")
            try:
                with urllib.request.urlopen(req, timeout=self.notifier_timeout) as r:
                    status_code = getattr(r, "status", None) or r.getcode()
                    resp_headers = dict(r.getheaders())
                    body_bytes = r.read() or b""
                    # tenta decodificar como JSON, senão mostra como texto
                    try:
                        body_decoded = json.loads(body_bytes.decode("utf-8") or "null")
                    except Exception:
                        body_decoded = body_bytes.decode("utf-8", errors="replace")

                    print(f"[notify] ✅ Sucesso")
                    print(f"[notify] Status: {status_code}")
                    print(f"[notify] Headers: {resp_headers}")
                    print(f"[notify] Body: {body_decoded}")

                    return

            except urllib.error.HTTPError as e:
                # HTTPError tem status e body
                last_exc = e
                err_body = e.read() or b""
                try:
                    err_decoded = json.loads(err_body.decode("utf-8") or "null")
                except Exception:
                    err_decoded = err_body.decode("utf-8", errors="replace")

                print(f"[notify] ❌ HTTPError")
                print(f"[notify] Status: {e.code}")
                print(f"[notify] Reason: {e.reason}")
                print(f"[notify] Headers: {dict(e.headers.items()) if e.headers else {}}")
                print(f"[notify] Body: {err_decoded}")

            except urllib.error.URLError as e:
                last_exc = e
                print(f"[notify] ❌ URLError")
                print(f"[notify] Reason: {getattr(e, 'reason', e)}")

            except Exception as e:
                last_exc = e
                print(f"[notify] ❌ Exception inesperada: {type(e).__name__}: {e}")

            # backoff exponencial com teto
            sleep_s = min(2 ** (attempt - 1), 4)
            print(f"[notify] Aguardando {sleep_s}s para retry...")
            time.sleep(sleep_s)

        logger.warning(f"[notify] falha ao notificar job={job_id}: {last_exc}")
        print(f"[notify] ❗ Falha definitiva ao notificar job={job_id}. Último erro: {last_exc}")
        return
