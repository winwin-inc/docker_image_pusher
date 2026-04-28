"""Delete 命令

通过 Registry API 批量删除镜像标签，无需浏览器。
"""

import re
import sys

import typer
from typer import Argument, Option

from ..registry.tags import delete_tag as api_delete_tag
from ..registry.tags import get_image_tags


def delete(
    tag: str = Argument(None, help="要删除的标签"),
    batch: str = Option(None, "--batch", "-b", help="批量删除标签，用空格分隔"),
    regex: str = Option(None, "--regex", "-r", help="按正则表达式匹配删除标签"),
    dry_run: bool = Option(False, "--dry-run", help="预览模式，不实际删除"),
    force: bool = Option(False, "--force", help="跳过确认提示"),
    limit: int = Option(100, "--limit", "-l", help="正则匹配删除数量限制"),
):
    """删除镜像标签

    使用 Registry API 直接删除，速度快且无需登录。

    示例:
        cli.py delete v1.0.0
        cli.py delete --batch "v1.0.0 v1.0.1 v1.0.2"
        cli.py delete --batch "$(cat tags.txt)"
        cli.py delete --regex "^test-.*"
    """
    # 单个删除
    if tag is not None:
        _delete_single(tag, dry_run)
        return

    # 批量删除
    if batch is not None:
        tag_list = batch.split()
        _delete_batch(tag_list, dry_run, force)
        return

    # 正则删除
    if regex is not None:
        _delete_regex(regex, dry_run, limit)
        return

    # 无参数
    print("错误: 请提供标签或使用 --batch / --regex 选项", file=sys.stderr)
    sys.exit(1)


def _delete_single(tag, dry_run):
    """删除单个标签"""
    if dry_run:
        print(f"[DRY-RUN] 将删除标签: {tag}")
        return

    result = api_delete_tag(tag)
    if result == "deleted":
        print(f"✓ 删除成功: {tag}")
    elif result == "not_found":
        print(f"  tag '{tag}' 不存在（已删除或从未推送）")
    else:
        print(f"✗ 删除失败: {tag}", file=sys.stderr)
        sys.exit(1)


def _delete_batch(tag_list, dry_run, force):
    """批量删除标签"""
    if not tag_list:
        print("错误: 请提供至少一个标签", file=sys.stderr)
        sys.exit(1)

    if not dry_run and not force:
        typer.confirm(f"确认删除以下 {len(tag_list)} 个标签?", abort=True)

    if dry_run:
        print(f"[DRY-RUN] 将批量删除 {len(tag_list)} 个标签:")
        for tag in tag_list:
            print(f"  - {tag}")
        return

    success_count, not_found_count, failed_count, failed_tags = _delete_batch_api(tag_list)
    _print_batch_results(success_count, not_found_count, failed_count, failed_tags)
    if failed_count > 0:
        sys.exit(1)


def _delete_batch_api(tag_list):
    """通过 Registry API 批量删除"""
    success_count = 0
    not_found_count = 0
    failed_count = 0
    failed_tags = []

    for i, tag in enumerate(tag_list):
        if (i + 1) % 10 == 0:
            print(f"进度: {i + 1}/{len(tag_list)}")
        result = api_delete_tag(tag)
        if result == "deleted":
            success_count += 1
        elif result == "not_found":
            not_found_count += 1
        else:
            failed_count += 1
            failed_tags.append(tag)

    return success_count, not_found_count, failed_count, failed_tags


def _delete_regex(pattern, dry_run, limit):
    """按正则表达式删除标签"""
    all_tags = get_image_tags()
    if not all_tags:
        print("无法获取标签列表", file=sys.stderr)
        sys.exit(1)

    try:
        compiled = re.compile(pattern)
    except re.error as e:
        print(f"正则表达式错误: {e}", file=sys.stderr)
        sys.exit(1)

    matched = [t for t in all_tags if compiled.search(t)]
    if len(matched) > limit:
        matched = matched[:limit]
        print(f"匹配结果超过限制 {limit}，仅处理前 {limit} 个", file=sys.stderr)

    if not matched:
        print("没有匹配到任何标签")
        return

    if dry_run:
        print(f"[DRY-RUN] 将删除 {len(matched)} 个匹配的标签:")
        for tag in matched:
            print(f"  - {tag}")
        return

    success_count, not_found_count, failed_count, failed_tags = _delete_batch_api(matched)
    _print_batch_results(success_count, not_found_count, failed_count, failed_tags)
    if failed_count > 0:
        sys.exit(1)


def _print_batch_results(success_count, not_found_count, failed_count, failed_tags):
    """打印批量删除结果"""
    print("\n删除结果:")
    print(f"  成功删除: {success_count}")
    print(f"  不存在:   {not_found_count}")
    if failed_count > 0:
        print(f"  失败:     {failed_count}")
        print(f"  失败的标签: {', '.join(failed_tags)}")


def register(app: typer.Typer):
    """注册 delete 命令"""
    app.command(name="delete")(delete)
