from app.domain.ports.repository import VideoRepositoryPort, JobRepositoryPort


class GoodVideoRepo:
    def __init__(self):
        self._store = {}

    def add(self, v):
        self._store[getattr(v, "id", "vid")] = v

    def get(self, video_id):
        return self._store.get(video_id)


class MissingGetVideoRepo:
    def add(self, v):
        pass


class GoodJobRepo:
    def __init__(self):
        self._store = {}
        self._by_user = {}

    def add(self, j):
        self._store[getattr(j, "id", "jid")] = j
        uid = getattr(j, "user_id", "u")
        self._by_user.setdefault(uid, []).append(j)

    def get(self, job_id):
        return self._store.get(job_id)

    def update(self, j):
        # sobrescreve por id
        self._store[getattr(j, "id", "jid")] = j

    def list_by_user(self, user_id):
        return list(self._by_user.get(user_id, []))


class MissingUpdateJobRepo:
    def add(self, j):
        pass

    def get(self, job_id):
        return None

    # faltando update
    def list_by_user(self, user_id):
        return []


# --- Tests para VideoRepositoryPort ---


def test_video_repository_port_runtime_checks_and_duck_typing():
    good = GoodVideoRepo()

    assert isinstance(good, VideoRepositoryPort)
    assert issubclass(GoodVideoRepo, VideoRepositoryPort)

    assert not isinstance(MissingGetVideoRepo(), VideoRepositoryPort)
    assert not issubclass(MissingGetVideoRepo, VideoRepositoryPort)

    class V:
        pass

    v = V()
    v.id = "v1"
    good.add(v)
    assert good.get("v1") is v


# --- Tests para JobRepositoryPort ---


def test_job_repository_port_runtime_checks_and_duck_typing():
    good = GoodJobRepo()

    assert isinstance(good, JobRepositoryPort)
    assert issubclass(GoodJobRepo, JobRepositoryPort)

    bad = MissingUpdateJobRepo()
    assert not isinstance(bad, JobRepositoryPort)
    assert not issubclass(MissingUpdateJobRepo, JobRepositoryPort)

    class J:
        pass

    j1 = J()
    j1.id = "j1"
    j1.user_id = "u1"
    j2 = J()
    j2.id = "j2"
    j2.user_id = "u1"

    good.add(j1)
    good.add(j2)

    assert good.get("j1") is j1
    assert good.get("j2") is j2

    j1b = J()
    j1b.id = "j1"
    j1b.user_id = "u1"
    j1b.changed = True
    good.update(j1b)
    assert good.get("j1") is j1b
    assert getattr(good.get("j1"), "changed", False) is True

    listed = list(good.list_by_user("u1"))
    assert {getattr(x, "id") for x in listed} == {"j1", "j2"}

    assert list(good.list_by_user("nobody")) == []
