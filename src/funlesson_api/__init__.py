"""funlesson —— 课程视频链接转大纲/思维导图/PPT/架构图的后端服务。"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("funlesson-api")
except PackageNotFoundError:
    __version__ = "0.0.0"
