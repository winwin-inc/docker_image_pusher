"""浏览器正则删除命令模块

实现使用浏览器按正则表达式删除标签的功能。
"""
import os
import sys

import typer
from typer import Argument, Option

from ...browser.deleter import AliyunBrowserDeleter


def register(app: typer.Typer):
    """注册 delete-browser-regex 命令

    Args:
        app: Typer 应用实例
    """

    @app.command(name="delete-browser-regex")
    def delete_browser_regex(
        pattern: str = Argument(..., help="正则表达式模式"),
        dry_run: bool = Option(False, "--dry-run", help="预览模式，不实际删除"),
        force: bool = Option(False, "--force", help="跳过确认提示"),
        show_browser: bool = Option(False, "--show-browser", help="显示浏览器窗口"),
        limit: int = Option(100, "--limit", "-l", help="限制删除数量")
    ):
        """使用浏览器自动化按正则表达式批量删除标签

        通过浏览器自动化技术访问阿里云控制台，按正则表达式匹配并删除标签。

        示例:
            cli.py delete-browser-regex "^test-.*"
            cli.py delete-browser-regex "^test-.*" --dry-run
            cli.py delete-browser-regex "2025.*" --force
            cli.py delete-browser-regex "^v1\\.0\\..*$" --limit 50
        """
        storage_state_path = os.getenv(
            "ALIYUN_STATE_PATH",
            "data/aliyun_state.json"
        )

        # 预览模式
        if dry_run:
            print(f"[DRY-RUN] 将使用浏览器按正则表达式删除标签:")
            print(f"[DRY-RUN] 模式: {pattern}")
            print(f"[DRY-RUN] 限制: {limit}")
            print(f"[DRY-RUN] 登录状态文件: {storage_state_path}")
            print(f"[DRY-RUN] 显示浏览器: {show_browser}")
            return

        # 创建删除器并执行删除
        with AliyunBrowserDeleter(
            storage_state_path=storage_state_path,
            headless=not show_browser
        ) as deleter:
            results = deleter.delete_regex_tags(pattern, limit=limit)

            if not results:
                print("没有删除任何标签")
                return

            # 统计结果
            success_count = sum(1 for v in results.values() if v)
            failed_count = len(results) - success_count

            print(f"\n删除结果:")
            print(f"  匹配: {len(results)}")
            print(f"  成功: {success_count}")
            print(f"  失败: {failed_count}")

            if failed_count > 0:
                sys.exit(1)
