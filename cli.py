"""兼容性入口 - 重定向到新的模块结构

此文件保留向后兼容性，实际功能已迁移到 src/ 目录。
"""
from src.main import app

if __name__ == "__main__":
    app()
