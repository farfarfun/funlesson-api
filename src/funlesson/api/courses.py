import os
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .. import jobs, storage

router = APIRouter(prefix="/api/courses", tags=["courses"])


class CreateCourseRequest(BaseModel):
    url: str


@router.post("")
def create_course(req: CreateCourseRequest, background_tasks: BackgroundTasks):
    job_id = uuid.uuid4().hex[:12]
    storage.create_job(job_id, req.url)
    background_tasks.add_task(jobs.run_pipeline, job_id, req.url)
    return {"id": job_id, "status": "pending"}


@router.get("/{job_id}")
def get_course(job_id: str):
    job = storage.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    response = {
        "id": job["id"],
        "url": job["url"],
        "status": job["status"],
        "step": job["step"],
        "error": job["error"],
    }
    if job["status"] == "done":
        response["result"] = storage.load_result(job_id)
    return response


@router.get("/{job_id}/ppt")
def download_ppt(job_id: str):
    job = storage.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="任务尚未完成")

    path = storage.ppt_path(job_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PPT 文件不存在")
    return FileResponse(
        path,
        filename="slides.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@router.get("/{job_id}/transcript")
def get_transcript(job_id: str):
    job = storage.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    result = storage.load_result(job_id)
    if result is None:
        raise HTTPException(status_code=409, detail="任务尚未完成")
    return {"transcript": result.get("transcript")}
