# funlesson

Funlesson 后端服务，面向教师备课场景：把课程视频链接转成结构化的大纲、思维导图、PPT 和架构图。
核心处理逻辑在 [funlesson-api](https://github.com/farfarfun/funlesson-api)，这里只是 FastAPI 封装。

配套 Web 界面见 [funlesson-web](https://github.com/farfarfun/funlesson-web)。

## 功能特性

- 提交课程视频链接，异步处理并可轮询进度
- 产出：转写文字稿、结构化大纲、思维导图（markmap 文本）、PPT（可下载）、架构图（Mermaid 文本）

## 快速开始

### 安装

开发环境下 `funlesson-api` 还没发布到 PyPI，需要先以可编辑模式装好：

```bash
pip install -e ../funlesson-api
pip install -e .
```

### 环境要求

同 [funlesson-api 的环境要求](https://github.com/farfarfun/funlesson-api#环境要求)：
系统需要 `ffmpeg`，本机需要已登录的 Claude Code CLI（`claude` 命令）。

### 运行

```bash
uvicorn funlesson.main:app --reload --port 8000
```

任务产物默认落盘到 `./data`，可通过环境变量 `FUNLESSON_DATA_DIR` 修改。

## API 文档

见 [`doc/API.md`](doc/API.md)。

## 开发指南

```bash
pytest
```

测试通过 monkeypatch 替换 `funlesson_api.pipeline.process`，不依赖真实下载/转写/claude 调用。

## 变更日志

见 [`CHANGELOG.md`](CHANGELOG.md)。

## 许可证

MIT
