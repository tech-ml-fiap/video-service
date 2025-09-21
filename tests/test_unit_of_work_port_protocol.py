from app.domain.ports.uow import UnitOfWorkPort
import pytest



class DummyVideoRepo:
    def __init__(self):
        self.add_calls = []
        self._by_id = {}

    def add(self, v):
        self.add_calls.append(v)
        vid = getattr(v, "id", None)
        if vid is not None:
            self._by_id[vid] = v

    def get(self, video_id):
        return self._by_id.get(video_id)


class DummyJobRepo:
    def __init__(self):
        self.add_calls = []
        self._by_id = {}
        self._by_user = {}

    def add(self, j):
        self.add_calls.append(j)
        jid = getattr(j, "id", None)
        uid = getattr(j, "user_id", None)
        if jid is not None:
            self._by_id[jid] = j
        if uid is not None:
            self._by_user.setdefault(uid, []).append(j)

    def get(self, job_id):
        return self._by_id.get(job_id)

    def update(self, j):
        jid = getattr(j, "id", None)
        if jid is not None:
            self._by_id[jid] = j

    def list_by_user(self, user_id):
        return list(self._by_user.get(user_id, []))


class ImplOK:
    def __init__(self):
        self.videos = DummyVideoRepo()
        self.jobs = DummyJobRepo()
        self.entered = False
        self.exited = False
        self.exit_args = None
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited = True
        self.exit_args = (exc_type, exc, tb)
        if exc_type is not None:
            self.rollback()
        return False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class MissingCommit:
    def __init__(self):
        self.videos = DummyVideoRepo()
        self.jobs = DummyJobRepo()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def rollback(self):
        pass


class MissingRepos:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def commit(self):
        pass
    def rollback(self):
        pass


def use_uow_happy(uow: UnitOfWorkPort):
    with uow as tx:
        class V: pass
        v = V(); v.id = "v1"
        tx.videos.add(v)

        class J: pass
        j = J(); j.id = "j1"; j.user_id = "u1"
        tx.jobs.add(j)

        tx.commit()
    return True


def use_uow_raises(uow: UnitOfWorkPort):
    with uow as tx:
        raise RuntimeError("boom")


def test_duck_typing_happy_path_calls_repos_and_commit():
    uow = ImplOK()
    assert use_uow_happy(uow) is True

    assert uow.entered is True
    assert uow.exited is True
    et, e, tb = uow.exit_args
    assert et is None and e is None and tb is None

    assert uow.videos.get("v1") is not None
    assert uow.jobs.get("j1") is not None
    assert uow.committed is True
    assert uow.rolled_back is False


def test_duck_typing_on_exception_triggers_rollback_and_reraises():
    uow = ImplOK()
    with pytest.raises(RuntimeError, match="boom"):
        use_uow_raises(uow)

    assert uow.exited is True
    et, e, tb = uow.exit_args
    assert et is RuntimeError
    assert isinstance(e, RuntimeError)
    assert uow.rolled_back is True
    assert uow.committed is False


def test_missing_commit_method_raises_attribute_error():
    uow = MissingCommit()
    with pytest.raises(AttributeError):
        use_uow_happy(uow)


def test_missing_repos_raise_attribute_error_on_use():
    uow = MissingRepos()
    with pytest.raises(AttributeError):
        use_uow_happy(uow)


def test_isinstance_and_issubclass_are_not_allowed_without_runtime_checkable():
    with pytest.raises(TypeError):
        isinstance(ImplOK(), UnitOfWorkPort)  # noqa: B015
    with pytest.raises(TypeError):
        issubclass(ImplOK, UnitOfWorkPort)    # noqa: B015
