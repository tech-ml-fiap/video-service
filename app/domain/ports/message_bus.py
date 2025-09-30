from typing import Protocol


class MessageBusPort(Protocol):
    def enqueue_process(self, job_id: str) -> None: ...
