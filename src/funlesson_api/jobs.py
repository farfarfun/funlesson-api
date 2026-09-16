"""后台任务：调用 funlesson 的处理管线，把进度和结果写回任务存储。"""

import logging

from funlesson import pipeline

from . import storage

logger = logging.getLogger("funlesson")


def run_pipeline(job_id: str, url: str) -> None:
    storage.update_status(job_id, status="running", step="fetch")

    def on_progress(step: str) -> None:
        storage.update_status(job_id, status="running", step=step)

    try:
        note = pipeline.process(url, storage.job_dir(job_id), on_progress=on_progress)
    except Exception as e:
        logger.exception("课程处理失败: job_id=%s url=%s", job_id, url)
        storage.update_status(job_id, status="failed", step=None, error=str(e))
        return

    storage.save_result(job_id, note)
    storage.update_status(job_id, status="done", step=None)
