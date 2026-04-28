"""浏览器批量删除命令模块

实现使用浏览器批量删除标签的功能。
"""
import os
import sys

import typer
from typer import Argument, Option

from ...browser.deleter import AliyunBrowserDeleter


def register(app: typer.Typer):
    """注册 delete-browser-batch 命令

    Args:
        app: Typer 应用实例
    """

    @app.command(name="delete-browser-batch")
    def delete_browser_batch(
        tags: str = Argument(..., help="要删除的标签，用空格分隔"),
        dry_run: bool = Option(False, "--dry-run", help="预览模式，不实际删除"),
        force: bool = Option(False, "--force", help="跳过确认提示"),
        show_browser: bool = Option(False, "--show-browser", help="显示浏览器窗口"),
        delay: float = Option(2.0, "--delay", help="操作之间的延迟时间(秒)")
    ):
        """使用浏览器自动化批量删除标签

        通过浏览器自动化技术访问阿里云控制台，批量删除指定的镜像标签。

        示例:
            cli.py delete-browser-batch "v1.0.0 v1.0.1 v1.0.2"
            cli.py delete-browser-batch "v1.0.0 v1.0.1" --force
            cli.py delete-browser-batch "v1.0.0 v1.0.1" --show-browser
        """
        tag_list = tags.split()
        if not tag_list:
            typer.echo("错误: 请提供至少一个标签", err=True)
            sys.exit(1)

        if not dry_run and not force:
            typer.confirm(f"确认使用浏览器删除以下 {len(tag_list)} 个标签?", abort=True)

        storage_state_path = os.getenv(
            "ALIYUN_STATE_PATH",
            "data/aliyun_state.json"
        )

        # 预览模式
        if dry_run:
            print(f"[DRY-RUN] 将使用浏览器批量删除 {len(tag_list)} 个标签:")
            for tag in tag_list:
                print(f"  - {tag}")
            print(f"[DRY-RUN] 登录状态文件: {storage_state_path}")
            print(f"[DRY-RUN] 显示浏览器: {show_browser}")
            return

        # 创建删除器并执行删除
        with AliyunBrowserDeleter(
            storage_state_path=storage_state_path,
            headless=not show_browser,
            delay=delay
        ) as deleter:
            results = deleter.delete_batch_tags(tag_list)

            # 统计结果
            success_count = sum(1 for v in results.values() if v)
            failed_count = len(results) - success_count

            print(f"\n删除结果:")
            print(f"  成功: {success_count}")
            print(f"  失败: {failed_count}")

            # 显示失败的标签
            failed_tags = [tag for tag, success in results.items() if not success]
            if failed_tags:
                print(f"  失败的标签: {', '.join(failed_tags)}")

            if failed_count > 0:
                sys.exit(1)
