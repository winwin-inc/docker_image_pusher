"""浏览器单个删除命令模块

实现使用浏览器删除单个标签的功能。
"""
import os
import sys

import typer
from typer import Argument, Option

from ...browser.deleter import AliyunBrowserDeleter


def register(app: typer.Typer):
    """注册 delete-browser-single 命令

    Args:
        app: Typer 应用实例
    """

    @app.command(name="delete-browser-single")
    def delete_browser_single(
        tag: str = Argument(..., help="要删除的标签"),
        dry_run: bool = Option(False, "--dry-run", help="预览模式，不实际删除"),
        show_browser: bool = Option(False, "--show-browser", help="显示浏览器窗口")
    ):
        """使用浏览器自动化删除单个标签

        通过浏览器自动化技术访问阿里云控制台，定位并删除指定的镜像标签。
        适用于 API 删除权限受限的场景。

        示例:
            cli.py delete-browser-single v1.0.0
            cli.py delete-browser-single v1.0.0 --dry-run
            cli.py delete-browser-single v1.0.0 --show-browser
        """
        storage_state_path = os.getenv(
            "ALIYUN_STATE_PATH",
            "data/aliyun_state.json"
        )

        # 预览模式
        if dry_run:
            print(f"[DRY-RUN] 将使用浏览器删除标签: {tag}")
            print(f"[DRY-RUN] 登录状态文件: {storage_state_path}")
            print(f"[DRY-RUN] 显示浏览器: {show_browser}")
            return

        # 创建删除器并执行删除
        with AliyunBrowserDeleter(
            storage_state_path=storage_state_path,
            headless=not show_browser
        ) as deleter:
            success = deleter.delete_single_tag(tag)

            if success:
                print(f"✓ 成功删除标签: {tag}")
            else:
                print(f"✗ 删除失败: {tag}")
                sys.exit(1)
