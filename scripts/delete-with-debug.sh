#!/bin/bash
# 启用 DEBUG 日志的删除脚本

# 加载环境变量
export $(cat .env.beijing | xargs)

# 设置日志级别为 DEBUG
export LOG_LEVEL=DEBUG

# 运行命令
PYTHONPATH=. uv run cli.py delete-browser-single "$@" --show-browser
