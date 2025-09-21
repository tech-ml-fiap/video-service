import io, os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import FileResponse
from app.adapters.driver.api.dependencies import CurrentUser, get_current_user
from app.config.container import get_enqueue_service, get_status_service, get_list_jobs_service, get_storage

router = APIRouter()

@router.post("/videos", status_code=202)
async def enqueue_video(file: UploadFile = File(...), fps: int = 1, user: CurrentUser = Depends(get_current_user)):
    service = get_enqueue_service()
    data = await file.read()
    job_id = service(user_id=user.user_id, file_stream=io.BytesIO(data), filename=file.filename, fps=fps)
    return {"job_id": job_id, "status": "queued"}

@router.get("/videos/{job_id}")
def get_status(job_id: str, user: CurrentUser = Depends(get_current_user)):
    service = get_status_service()
    try:
        return service(job_id=job_id, user_id=user.user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Process not found")

@router.get("/videos")
def list_jobs(user: CurrentUser = Depends(get_current_user)):
    service = get_list_jobs_service()
    return service(user_id=user.user_id)

@router.get("/download/{job_id}")
def download(job_id: str, user: CurrentUser = Depends(get_current_user)):
    status_service = get_status_service()
    try:
        data = status_service(job_id=job_id, user_id=user.user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Process not found")
    artifact_ref = data.get("artifact_ref")
    if not artifact_ref:
        raise HTTPException(status_code=400, detail="ZIP not ready")
    storage = get_storage()
    path = storage.resolve_path(artifact_ref)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Artifact missing")
    return FileResponse(path, filename=os.path.basename(path), media_type="application/zip")
