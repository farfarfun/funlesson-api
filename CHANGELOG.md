# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/) 格式。

## [未发布]

### Changed

- **破坏性变更**：包名从 `funlesson` 改为 `funlesson-api`（仓库同步改名），核心库仓库改名
  为 `funlesson`，按 `submodule-workspace-governance` 规范对齐 `<product>-api` 命名
- README 里的默认运行端口改为 `18812`，配合 `funlesson-web` 的内置反代服务

### Added

- `funlesson-api` CLI（`[project.scripts]`），服务生命周期命令 `server run/start/stop/restart/status`，
  逻辑照搬 funflix，默认端口 `18812`

## [0.1.0] - 2026-09-16

### Added

- FastAPI 服务，封装 `funlesson` 的处理管线
- `POST /api/courses` 提交课程链接，后台任务异步处理，SQLite 存任务状态
- `GET /api/courses/{id}`、`GET /api/courses/{id}/ppt`、`GET /api/courses/{id}/transcript`
