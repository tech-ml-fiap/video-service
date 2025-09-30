import uuid
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.adapters.driven.db.models import Base


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite+pysqlite:///:memory:", future=True)

    @event.listens_for(eng, "connect")
    def _enable_fk(dbapi_con, _):
        cur = dbapi_con.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(eng)


@pytest.fixture()
def Session(engine):
    return sessionmaker(bind=engine, future=True)


@pytest.fixture()
def session(Session):
    with Session() as s:
        yield s


@pytest.fixture()
def uid():
    return lambda: str(uuid.uuid4())
