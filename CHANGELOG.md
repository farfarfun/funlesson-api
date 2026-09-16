# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/) 格式。

## [0.1.0] - 2026-09-16

### Added

- FastAPI 服务，封装 `funlesson-api` 的处理管线
- `POST /api/courses` 提交课程链接，后台任务异步处理，SQLite 存任务状态
- `GET /api/courses/{id}`、`GET /api/courses/{id}/ppt`、`GET /api/courses/{id}/transcript`
