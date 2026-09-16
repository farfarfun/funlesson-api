# funlesson-api

Funlesson 后端服务，面向教师备课场景：把课程视频链接转成结构化的大纲、思维导图、PPT 和架构图。
核心处理逻辑在 [funlesson](https://github.com/farfarfun/funlesson)，这里只是 FastAPI 封装。

配套 Web 界面见 [funlesson-web](https://github.com/farfarfun/funlesson-web)。

## 功能特性

- 提交课程视频链接，异步处理并可轮询进度
- 产出：转写文字稿、结构化大纲、思维导图（markmap 文本）、PPT（可下载）、架构图（Mermaid 文本）

## 快速开始

### 环境要求

同 [funlesson 的环境要求](https://github.com/farfarfun/funlesson#环境要求)：
系统需要 `ffmpeg`，本机需要已登录的 Claude Code CLI（`claude` 命令）。

### 安装

包发布在私有 index（组织私有 PyPI，非公开 pypi.org），需要组织账号密码（找管理员要，
不要把密码提交进仓库）；该 index 不代理公网包，`fastapi`/`uvicorn` 等公开依赖需要额外
指定公网 index：

```bash
pip install funlesson-api \
    --index-url https://<user>:<password>@packages.aliyun.com/5fc5eb115dbd287006145e5f/pypi/funpy/simple/ \
    --extra-index-url https://pypi.org/simple
```

### 运行

生产/常规用法，`funlesson-api` 自带服务生命周期命令：

```bash
funlesson-api server start --host 0.0.0.0 --port 18812
funlesson-api server status
funlesson-api server stop
funlesson-api server restart
```

调试用前台模式（`--reload` 开发时自动重载）：

```bash
funlesson-api server run --reload --port 18812
```

也可以不装 CLI、直接用 uvicorn：

```bash
uvicorn funlesson_api.main:app --reload --port 18812
```

`server` 各命令默认监听 `127.0.0.1:18812`，`--host`/`--port`/`--config` 可覆盖；
`--config` 缺省时读 `${XDG_CONFIG_HOME:-~/.config}/farfarfun/funlesson-api/config.toml`。
`start` 写的 PID 文件（`server.pid`）和日志（`server.log`）都放在同一个配置目录下。

任务产物默认落盘到 `./data`，可通过环境变量 `FUNLESSON_DATA_DIR` 修改。

### 从源码开发

```bash
pip install -e ../funlesson
pip install -e .
```

## API 文档

见 [`doc/API.md`](doc/API.md)。

## 开发指南

```bash
pytest
```

测试通过 monkeypatch 替换 `funlesson.pipeline.process`，不依赖真实下载/转写/claude 调用。

## 变更日志

见 [`CHANGELOG.md`](CHANGELOG.md)。

## 许可证

MIT
