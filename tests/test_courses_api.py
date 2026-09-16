from fastapi.testclient import TestClient

from funlesson_api import jobs as jobs_module
from funlesson_api import storage
from funlesson_api.main import app
from funlesson.models import (
    DiagramSpec,
    MediaInfo,
    Note,
    Outline,
    OutlineNode,
    Transcript,
)


def _fake_note(url: str) -> Note:
    return Note(
        media=MediaInfo(
            url=url, title="示例课程", duration=60.0, cover=None, audio_path="/tmp/audio.mp3"
        ),
        transcript=Transcript(full_text="这是转写文本", segments=[]),
        outline=Outline(
            title="示例课程", nodes=[OutlineNode(title="第一章", start=0.0, children=[])]
        ),
        mindmap="# 示例课程\n- 第一章（00:00）",
        diagrams=[DiagramSpec(title="流程图", mermaid="flowchart TD\n  A --> B")],
        ppt_path="/tmp/slides.pptx",
    )


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(storage, "DB_PATH", str(tmp_path / "jobs.db"))
    return TestClient(app)


def test_create_and_fetch_course(tmp_path, monkeypatch):
    def fake_process(url, workdir, on_progress=None):
        if on_progress:
            on_progress("outline")
        return _fake_note(url)

    monkeypatch.setattr(jobs_module.pipeline, "process", fake_process)

    with _client(tmp_path, monkeypatch) as client:
        create_resp = client.post("/api/courses", json={"url": "https://example.com/video"})
        assert create_resp.status_code == 200
        body = create_resp.json()
        assert body["status"] == "pending"
        job_id = body["id"]

        detail = client.get(f"/api/courses/{job_id}").json()
        assert detail["status"] == "done"
        assert detail["result"]["outline"]["title"] == "示例课程"
        assert "audio_path" not in detail["result"]["media"]


def test_get_unknown_course_returns_404(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        resp = client.get("/api/courses/does-not-exist")
        assert resp.status_code == 404


def test_failed_pipeline_reports_error(tmp_path, monkeypatch):
    def fake_process(url, workdir, on_progress=None):
        raise RuntimeError("下载失败")

    monkeypatch.setattr(jobs_module.pipeline, "process", fake_process)

    with _client(tmp_path, monkeypatch) as client:
        job_id = client.post("/api/courses", json={"url": "https://example.com/bad"}).json()["id"]
        detail = client.get(f"/api/courses/{job_id}").json()
        assert detail["status"] == "failed"
        assert detail["error"] == "下载失败"
