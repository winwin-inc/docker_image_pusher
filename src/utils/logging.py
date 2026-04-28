"""日志配置模块

提供统一的日志配置功能。
"""
import logging
import logging.config
import os
from datetime import datetime


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    max_bytes: int = 1024 * 1024 * 5,  # 5MB
    backup_count: int = 10,
    use_json: bool = False,
):
    """配置项目日志系统

    Args:
        log_dir: 日志文件目录
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的备份文件数量
        use_json: 是否使用 JSON 格式（需要 python-json-logger）
    """
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)

    # 日志文件名（包含日期）
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"app-{today}.log")

    # 基础格式配置
    formatters = {
        "console": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d [PID:%(process)d TID:%(thread)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }

    # 如果需要JSON格式（推荐生产环境）
    if use_json:
        try:
            from pythonjsonlogger import (
                jsonlogger,
            )  # 需要安装: pip install python-json-logger

            formatters["file"] = {
                "()": jsonlogger.JsonFormatter,
                "fmt": "%(asctime)s %(levelname)s %(name)s %(lineno)d %(process)d %(thread)d %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        except ImportError:
            logging.warning("python-json-logger not installed, using plain text format")

    # 处理器配置
    handlers = {
        # 控制台输出（仅输出WARNING及以上级别）
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "console",
            "stream": "ext://sys.stdout",
        },
        # 文件输出（按大小轮转）
        "file_size": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "file",
            "filename": log_file,
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf-8",
        },
        # 可选：按时间轮转（每天一个文件）
        # "file_time": {
        #     "class": "logging.handlers.TimedRotatingFileHandler",
        #     "level": log_level,
        #     "formatter": "file",
        #     "filename": log_file,
        #     "when": "midnight",  # 每天凌晨轮转
        #     "interval": 1,
        #     "backupCount": 30,  # 保留30天
        #     "encoding": "utf-8"
        # }
    }

    # 根日志配置
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,  # 不覆盖已有logger
            "formatters": formatters,
            "handlers": handlers,
            "root": {
                "level": log_level,
                "handlers": ["console", "file_size"],  # 启用的处理器
            },
        }
    )
    logging.getLogger('apscheduler.scheduler').setLevel(logging.WARNING)
