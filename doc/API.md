# API 文档

所有接口前缀为 `/api/courses`。

## `POST /api/courses`

提交一条课程视频链接，创建处理任务。

请求体：

```json
{ "url": "https://www.bilibili.com/video/BVxxxxxxxx" }
```

响应：

```json
{ "id": "a1b2c3d4e5f6", "status": "pending" }
```

## `GET /api/courses/{id}`

查询任务状态与结果。`status` 取值：`pending` / `running` / `done` / `failed`；
`running` 时 `step` 依次为 `fetch` -> `asr` -> `outline` -> `mindmap` -> `ppt` -> `diagram`。

```json
{
  "id": "a1b2c3d4e5f6",
  "url": "...",
  "status": "done",
  "step": null,
  "error": null,
  "result": {
    "media": { "url": "...", "title": "...", "duration": 600.0, "cover": "..." },
    "transcript": { "full_text": "...", "segments": [{ "start": 0.0, "end": 3.2, "text": "..." }] },
    "outline": { "title": "...", "nodes": [{ "title": "...", "start": 0.0, "children": [] }] },
    "mindmap": "# 标题\n- 一级标题（00:00）",
    "diagrams": [{ "title": "...", "mermaid": "flowchart TD\n  A --> B" }]
  }
}
```

`status=failed` 时 `error` 字段是失败原因。

## `GET /api/courses/{id}/ppt`

下载生成的 `slides.pptx`，任务未完成时返回 409。

## `GET /api/courses/{id}/transcript`

单独获取转写结果（`{"transcript": {...}}`），任务未完成时返回 409。
