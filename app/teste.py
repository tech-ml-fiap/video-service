from app.config.container import get_process_service

service = get_process_service()
service(job_id=job_id)
