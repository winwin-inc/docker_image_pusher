"""List 命令模块

实现列出已推送镜像的功能。
"""
import typer

from ..core.config import Config
from ..registry.tags import get_image_tags


def register(app: typer.Typer):
    """注册 list 命令

    Args:
        app: Typer 应用实例
    """

    @app.command()
    def list():
        """列出已推送的镜像"""
        tags = get_image_tags()
        registry = Config.get_registry()
        namespace = Config.get_namespace()

        for tag in tags:
            print(f"{registry}/{namespace}:{tag}")
