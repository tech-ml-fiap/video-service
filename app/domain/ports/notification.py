from abc import ABC, abstractmethod
from typing import Optional, Literal

Status = Literal["success", "error"]

class NotificationPort(ABC):
    @abstractmethod
    def notify(
        self,
        *,
        user_id: id,
        job_id: str,
        status: Status,
        video_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Dispara a notificação assíncrona. Não deve levantar exceção que quebre o fluxo do job."""
        ...
