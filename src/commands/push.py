"""Push 命令模块

实现推送新镜像的功能。
"""
import logging
import yaml
from pathlib import Path
from typing import Dict

import typer
from prettytable import PrettyTable

from ..core.config import Config
from ..image.parser import parse_image, get_image_tag
from ..image.pusher import push_image
from ..registry.tags import get_image_tags

logger = logging.getLogger(__name__)


def register(app: typer.Typer):
    """注册 push 命令

    Args:
        app: Typer 应用实例
    """

    @app.command()
    def push(dry_run: bool = False):
        """推送新镜像到阿里云"""
        table = PrettyTable()
        table.align = "l"
        table.field_names = ["image_name", "tag"]

        tags = get_image_tags()
        seen: Dict[str, str] = {}

        # 查找 images.yaml 文件
        yaml_path = Path("images.yaml")
        if not yaml_path.exists():
            logger.error("未找到 images.yaml 文件")
            return

        with open(yaml_path, "r") as file:
            images = yaml.safe_load(file)
            for image in images:
                image.update(parse_image(image["name"]))
                pushed = False

                for tag in get_image_tag(image):
                    if not tag:
                        continue

                    if tag in tags:
                        if tag not in seen:
                            seen[tag] = image["name"]
                            pushed = True
                            break
                        else:
                            continue
                    else:
                        tags.append(tag)
                        seen[tag] = image["name"]
                        push_image(image, tag, dry_run)
                        pushed = True
                        break

                if not pushed and image["name"] not in seen.values():
                    logger.error(f"image {image['name']} not pushed")

        for tag, name in seen.items():
            table.add_row([name, tag])

        print(table)
