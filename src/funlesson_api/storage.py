"""任务状态存取：一张 SQLite jobs 表 + 每个任务一个 data/<id>/ 产物目录。"""

import json
import os
import sqlite3
import threading
from dataclasses import asdict
from datetime import datetime, timezone

DATA_DIR = os.environ.get("FUNLESSON_DATA_DIR", os.path.join(os.getcwd(), "data"))
DB_PATH = os.path.join(DATA_DIR, "jobs.db")

_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _execute(sql: str, params: tuple = ()) -> None:
    with _lock:
        conn = _connect()
        try:
            with conn:
                conn.execute(sql, params)
        finally:
            conn.close()


def _query_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    conn = _connect()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def init_db() -> None:
    _execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            step TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    # CREATE TABLE IF NOT EXISTS 不会给已存在的库补列，已部署的 jobs.db 需要这一步
    # 幂等迁移才能拿到 progress 列；列已存在时 sqlite3 抛 OperationalError，忽略即可。
    try:
        _execute("ALTER TABLE jobs ADD COLUMN progress REAL")
    except sqlite3.OperationalError:
        pass


def job_dir(job_id: str) -> str:
    path = os.path.join(DATA_DIR, job_id)
    os.makedirs(path, exist_ok=True)
    return path


def ppt_path(job_id: str) -> str:
    return os.path.join(job_dir(job_id), "slides.pptx")


def result_path(job_id: str) -> str:
    return os.path.join(job_dir(job_id), "result.json")


def create_job(job_id: str, url: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    _execute(
        "INSERT INTO jobs (id, url, status, step, error, created_at, updated_at) "
        "VALUES (?, ?, 'pending', NULL, NULL, ?, ?)",
        (job_id, url, now, now),
    )


def update_status(
    job_id: str,
    *,
    status: str,
    step: str | None = None,
    error: str | None = None,
    progress: float | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    _execute(
        "UPDATE jobs SET status=?, step=?, error=?, progress=?, updated_at=? WHERE id=?",
        (status, step, error, progress, now, job_id),
    )


def get_job(job_id: str) -> dict | None:
    row = _query_one("SELECT * FROM jobs WHERE id=?", (job_id,))
    return dict(row) if row else None


def save_result(job_id: str, note) -> None:
    data = asdict(note)
    # 本地文件路径不对外暴露，前端走专门的下载接口
    data.pop("ppt_path", None)
    data["media"].pop("audio_path", None)
    with open(result_path(job_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_result(job_id: str) -> dict | None:
    path = result_path(job_id)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)
