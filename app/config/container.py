import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.driven.gateway.customer_auth_http import CustomerAuthHttp
from app.config.settings import settings
from app.adapters.driven.db.models import Base
from app.adapters.driven.db.sqlalchemy_uow import SQLAlchemyUnitOfWork
from app.adapters.driven.storage.local_storage import LocalStorage
from app.adapters.driven.broker.celery_bus import CeleryMessageBus
from app.adapters.driven.media.ffmpeg_processor import FFmpegVideoProcessor
from app.domain.services.enqueue_video import EnqueueVideoService
from app.domain.services.process_video import ProcessVideoService
from app.domain.services.query_jobs import GetJobStatusService, ListJobsByUserService

_engine = create_engine(settings.database_url, pool_pre_ping=True)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)

def get_uow():
    return SQLAlchemyUnitOfWork(_SessionLocal)

def get_storage():
    return LocalStorage(settings.storage_dir)

def get_bus():
    return CeleryMessageBus(settings.broker_url, settings.result_backend)

def get_processor():
    return FFmpegVideoProcessor()

def get_enqueue_service():
    return EnqueueVideoService(uow=get_uow(), storage=get_storage(), bus=get_bus())

def get_process_service():
    return ProcessVideoService(uow=get_uow(), storage=get_storage(), processor=get_processor())

def get_status_service():
    return GetJobStatusService(uow=get_uow())

def get_list_jobs_service():
    return ListJobsByUserService(uow=get_uow())

def get_auth_gateway():
    return CustomerAuthHttp(os.getenv("CUSTOMER_SERVICE_URL"))