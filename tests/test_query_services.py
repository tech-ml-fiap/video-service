from datetime import datetime, timedelta
import pytest

from app.domain.services.query_jobs import GetJobStatusService, ListJobsByUserService


class _Job:
    def __init__(
        self,
        id: str,
        video_id: str,
        user_id: str,
        status: str,
        fps: int,
        frame_count: int = 0,
        artifact_ref: str | None = None,
        error: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.video_id = video_id
        self.user_id = user_id
        self.status = status
        self.fps = fps
        self.frame_count = frame_count
        self.artifact_ref = artifact_ref
        self.error = error
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()


class _JobsRepo:
    def __init__(
        self,
        by_id: dict[str, _Job] | None = None,
        by_user: dict[str, list[_Job]] | None = None,
    ):
        self._by_id = by_id or {}
        self._by_user = by_user or {}

    def get(self, job_id: str) -> _Job | None:
        return self._by_id.get(job_id)

    def list_by_user(self, user_id: str):
        return list(self._by_user.get(user_id, []))


class _UoW:
    def __init__(self, jobs_repo: _JobsRepo):
        self.jobs = jobs_repo
        self.entered = 0
        self.exited = 0

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited += 1
        return False

    def commit(self):
        pass

    def rollback(self):
        pass


def test_get_job_status_success_returns_dict_with_iso_dates():
    created = datetime.utcnow() - timedelta(hours=1)
    updated = datetime.utcnow()
    job = _Job(
        id="j1",
        video_id="v1",
        user_id="alice",
        status="RUNNING",
        fps=3,
        frame_count=12,
        artifact_ref="/outputs/a.zip",
        error=None,
        created_at=created,
        updated_at=updated,
    )

    repo = _JobsRepo(by_id={"j1": job})
    uow = _UoW(repo)
    svc = GetJobStatusService(uow=uow)

    out = svc(job_id="j1", user_id="alice")

    assert out == {
        "job_id": "j1",
        "status": "RUNNING",
        "fps": 3,
        "frames": 12,
        "artifact_ref": "/outputs/a.zip",
        "error": None,
        "created_at": created.isoformat(),
        "updated_at": updated.isoformat(),
    }
    assert uow.entered == 1 and uow.exited == 1


@pytest.mark.parametrize(
    "job,user_id",
    [
        (None, "alice"),
        (_Job("j2", "v", "bob", "DONE", 1), "alice"),
    ],
)
def test_get_job_status_raises_keyerror_when_missing_or_user_mismatch(job, user_id):
    repo = _JobsRepo(by_id={"jX": job} if job else {})
    uow = _UoW(repo)
    svc = GetJobStatusService(uow=uow)

    with pytest.raises(KeyError):
        svc(job_id="jX", user_id=user_id)

    assert uow.entered == 1 and uow.exited == 1


def test_list_jobs_by_user_returns_sanitized_list_only_for_that_user():
    j1 = _Job("a", "v1", "carol", "QUEUED", 1, frame_count=0, artifact_ref=None)
    j2 = _Job("b", "v1", "carol", "DONE", 2, frame_count=42, artifact_ref="/out.zip")
    j_other = _Job("z", "v2", "dave", "RUNNING", 1)

    repo = _JobsRepo(
        by_user={
            "carol": [j2, j1],
            "dave": [j_other],
        }
    )
    uow = _UoW(repo)
    svc = ListJobsByUserService(uow=uow)

    out = svc(user_id="carol")

    assert out == [
        {
            "job_id": "b",
            "status": "DONE",
            "fps": 2,
            "frames": 42,
            "artifact_ref": "/out.zip",
        },
        {
            "job_id": "a",
            "status": "QUEUED",
            "fps": 1,
            "frames": 0,
            "artifact_ref": None,
        },
    ]
    assert uow.entered == 1 and uow.exited == 1


def test_list_jobs_by_user_empty_when_no_jobs():
    repo = _JobsRepo(by_user={"someone": []})
    uow = _UoW(repo)
    svc = ListJobsByUserService(uow=uow)

    assert svc(user_id="nobody") == []
    assert uow.entered == 1 and uow.exited == 1
