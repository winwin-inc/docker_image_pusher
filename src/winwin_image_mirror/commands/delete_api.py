"""API 删除命令模块

实现通过 Docker Registry API 删除镜像标签的功能。
"""

import logging
import re
import sys

import typer
from typer import Argument, Option

from ..registry.tags import delete_image_tag, get_image_tags

logger = logging.getLogger(__name__)


def register(app: typer.Typer):
    """注册所有 API 删除命令

    Args:
        app: Typer 应用实例
    """

    @app.command()
    def delete(
        tag: str = Argument(..., help="要删除的标签"),
        dry_run: bool = Option(False, "--dry-run", help="预览模式，不实际删除"),
    ):
        """删除单个镜像标签

        示例:
            cli.py delete v1.0.0
            cli.py delete v1.0.0 --dry-run
        """
        success = delete_image_tag(tag, dry_run=dry_run)
        if success:
            if dry_run:
                print("✓ 预览模式完成，未实际删除")
            else:
                print(f"✓ 成功删除标签: {tag}")
        else:
            print(f"✗ 删除失败: {tag}")
            sys.exit(1)

    @app.command()
    def delete_batch(
        tags: str = Argument(..., help="要删除的标签，用空格分隔"),
        dry_run: bool = Option(False, "--dry-run", help="预览模式，不实际删除"),
        force: bool = Option(False, "--force", help="跳过确认提示"),
    ):
        """批量删除多个镜像标签

        示例:
            cli.py delete-batch "v1.0.0 v1.0.1 v1.0.2" --dry-run
            cli.py delete-batch "v1.0.0 v1.0.1 v1.0.2"
            cli.py delete-batch "v1.0.0 v1.0.1" --force
        """
        tag_list = tags.split()
        if not tag_list:
            typer.echo("错误: 请提供至少一个标签", err=True)
            sys.exit(1)

        if not dry_run and not force:
            typer.confirm(f"确认删除以下 {len(tag_list)} 个标签?", abort=True)

        success_count = 0
        failed_count = 0
        failed_tags = []

        for tag in tag_list:
            if delete_image_tag(tag, dry_run=dry_run):
                success_count += 1
            else:
                failed_count += 1
                failed_tags.append(tag)

        # 输出统计
        print("\n删除结果:")
        print(f"  成功: {success_count}")
        print(f"  失败: {failed_count}")
        if failed_tags:
            print(f"  失败的标签: {', '.join(failed_tags)}")

        if failed_count > 0 and not dry_run:
            sys.exit(1)

    @app.command(name="delete-regex")
    def delete_regex(
        pattern: str = Argument(..., help="正则表达式模式"),
        dry_run: bool = Option(False, "--dry-run", help="预览模式，不实际删除"),
        force: bool = Option(False, "--force", help="跳过确认提示"),
        limit: int = Option(100, "--limit", "-l", help="限制删除数量"),
    ):
        """按正则表达式批量删除标签

        示例:
            cli.py delete-regex "^test-.*"
            cli.py delete-regex "^test-.*" --dry-run
            cli.py delete-regex "2025.*" --force
        """
        # 编译正则表达式
        try:
            regex = re.compile(pattern)
        except re.error as e:
            typer.echo(f"无效的正则表达式: {e}", err=True)
            sys.exit(1)

        # 获取所有标签
        all_tags = get_image_tags()
        if not all_tags:
            typer.echo("未找到任何标签", err=True)
            sys.exit(1)

        # 过滤匹配的标签
        matched_tags = [tag for tag in all_tags if regex.match(tag)]

        if not matched_tags:
            typer.echo(f"没有标签匹配模式: {pattern}")
            raise typer.Exit(0)

        # 限制数量
        if len(matched_tags) > limit:
            typer.echo(f"匹配到 {len(matched_tags)} 个标签，但限制为 {limit} 个")
            matched_tags = matched_tags[:limit]

        # 显示匹配的标签
        print(f"匹配到 {len(matched_tags)} 个标签:")
        for i, tag in enumerate(matched_tags[:10], 1):
            print(f"  {i}. {tag}")
        if len(matched_tags) > 10:
            print(f"  ... 还有 {len(matched_tags) - 10} 个")

        # 确认
        if not dry_run and not force:
            typer.confirm(f"\n确认删除以上 {len(matched_tags)} 个标签?", abort=True)

        # 批量删除
        success_count = 0
        failed_count = 0

        for tag in matched_tags:
            if delete_image_tag(tag, dry_run=dry_run):
                success_count += 1
            else:
                failed_count += 1

        # 输出统计
        print("\n删除结果:")
        print(f"  匹配: {len(matched_tags)}")
        print(f"  成功: {success_count}")
        print(f"  失败: {failed_count}")

        if failed_count > 0 and not dry_run:
            sys.exit(1)

    @app.command(name="list-delete")
    def list_delete(
        pattern: str = ".*", limit: int = Option(20, "--limit", "-l", help="限制显示数量")
    ):
        """列出可删除的标签（用于预览）

        示例:
            cli.py list-delete
            cli.py list-delete --pattern "^v1\\.0\\..*$"
            cli.py list-delete -l 50
        """
        # 编译正则表达式
        try:
            regex = re.compile(pattern)
        except re.error as e:
            typer.echo(f"无效的正则表达式: {e}", err=True)
            sys.exit(1)

        # 获取所有标签
        all_tags = get_image_tags()
        if not all_tags:
            typer.echo("未找到任何标签")
            raise typer.Exit(0)

        # 过滤匹配的标签
        matched_tags = [tag for tag in all_tags if regex.match(tag)]

        # 限制数量
        matched_tags = matched_tags[:limit]

        # 显示结果
        print(f"找到 {len(matched_tags)} 个匹配的标签:")
        for i, tag in enumerate(matched_tags, 1):
            print(f"  {i}. {tag}")

        if (
            len(matched_tags) == limit
            and len([tag for tag in all_tags if regex.match(tag)]) > limit
        ):
            print("  ... 还有更多标签（使用 --limit 增加显示数量）")
