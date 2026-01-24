"""镜像推送模块

提供镜像推送功能。
"""
import logging
import subprocess

from ..core.config import Config

logger = logging.getLogger(__name__)


def push_image(image: dict, tag: str, dry_run: bool = False) -> bool:
    """推送镜像到阿里云

    Args:
        image: 镜像信息字典（由 parse_image 返回）
        tag: 目标标签
        dry_run: 预览模式，不实际推送

    Returns:
        是否推送成功
    """
    logger.info(f"push image {image['name']} with tag {tag}")

    if dry_run:
        return True

    full_name = f"{Config.get_registry()}/{Config.get_namespace()}:{tag}"

    # TODO: 支持 platform 参数
    commands = f"""
    docker pull {image["name"]}
    docker tag {image["name"]} {full_name}
    docker push {full_name}
    docker rmi {image["name"]}
    docker rmi {full_name}
    """

    # 执行命令，将输出直接输出到当前的 stdout 和 stderr
    try:
        subprocess.run(["bash", "-c", commands], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败，返回码: {e.returncode}")
        return False
