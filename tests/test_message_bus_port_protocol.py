import pytest

from app.domain.ports.message_bus import MessageBusPort


def enqueue(bus: MessageBusPort, job_id: str) -> None:
    bus.enqueue_process(job_id)


class ImplOK:
    def __init__(self):
        self.called_with = None

    def enqueue_process(self, job_id: str) -> None:
        self.called_with = job_id


class MissingMethod:
    pass


def test_protocol_instance_and_subclass_checks_disallowed():
    with pytest.raises(TypeError):
        isinstance(ImplOK(), MessageBusPort)  # noqa: B015 (teste proposital)

    with pytest.raises(TypeError):
        issubclass(ImplOK, MessageBusPort)  # noqa: B015


def test_duck_typing_happy_path_calls_enqueue():
    bus = ImplOK()
    enqueue(bus, "job-123")
    assert bus.called_with == "job-123"


def test_duck_typing_missing_method_raises_attribute_error():
    with pytest.raises(AttributeError):
        enqueue(MissingMethod(), "job-xyz")
