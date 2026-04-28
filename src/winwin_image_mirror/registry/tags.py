"""Tag 操作模块

提供 Docker Registry API 的 Tag 操作功能。
"""

import logging
from typing import List, Optional

import httpx

from ..core.config import Config
from .auth import get_auth_token

logger = logging.getLogger(__name__)


def get_image_tags() -> List[str]:
    """获取镜像标签列表

    Returns:
        镜像标签列表，如果失败则返回空列表
    """
    token = get_auth_token("pull")
    if not token:
        return []

    try:
        namespace = Config.get_namespace()
        registry = Config.get_registry()
    except KeyError as e:
        logger.error(f"缺少环境变量: {e}")
        return []

    url = f"https://{registry}/v2/{namespace}/tags/list"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Docker-Distribution-Api-Version": "registry/2.0",
        "Authorization": f"Bearer {token}",
    }

    response = httpx.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["tags"]
    else:
        logger.error(f"请求失败，状态码: {response.status_code}")
        return []


def get_image_digest(
    tag: str, namespace: Optional[str] = None, token: Optional[str] = None
) -> Optional[str]:
    """获取镜像标签的 Docker-Content-Digest

    Args:
        tag: 镜像标签
        namespace: 命名空间，默认使用环境变量 ALIYUN_NAME_SPACE
        token: 认证 token（如果为 None 则自动获取）

    Returns:
        digest 字符串或 None
    """
    try:
        namespace = namespace or Config.get_namespace()
        registry = Config.get_registry()
    except KeyError as e:
        logger.error(f"缺少环境变量: {e}")
        return None

    # 如果没有提供 token，则获取 pull token
    if not token:
        token = get_auth_token("pull", namespace)
        if not token:
            logger.error("获取认证 token 失败")
            return None

    # 获取 manifest
    manifest_url = f"https://{registry}/v2/{namespace}/manifests/{tag}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json",
    }

    logger.debug(f"获取 manifest: {manifest_url}")
    response = httpx.get(manifest_url, headers=headers)

    if response.status_code == 200:
        digest = response.headers.get("Docker-Content-Digest")
        if digest:
            logger.debug(f"获取到 digest: {digest}")
            return digest
        else:
            logger.error("无法从响应头获取 Docker-Content-Digest")
            return None
    elif response.status_code == 404:
        logger.error(f"标签不存在: {tag}")
        return None
    else:
        logger.error(f"获取 manifest 失败，状态码: {response.status_code}")
        return None


def delete_image_tag(tag: str, namespace: Optional[str] = None, dry_run: bool = False) -> bool:
    """删除指定的镜像标签

    Args:
        tag: 要删除的标签
        namespace: 命名空间
        dry_run: 预览模式，不实际删除

    Returns:
        是否删除成功
    """
    try:
        namespace = namespace or Config.get_namespace()
        registry = Config.get_registry()
    except KeyError as e:
        logger.error(f"缺少环境变量: {e}")
        return False

    prefix = "[DRY-RUN] " if dry_run else ""
    logger.info(f"{prefix}准备删除标签: {tag}")

    # 获取 delete 权限的 token
    delete_token = get_auth_token("delete", namespace)
    if not delete_token:
        logger.error("获取删除权限 token 失败")
        return False

    # 获取 digest
    digest = get_image_digest(tag, namespace)
    if not digest:
        logger.error(f"无法获取标签 {tag} 的 digest")
        return False

    logger.debug(f"标签 {tag} 的 digest: {digest}")

    if dry_run:
        logger.info(f"{prefix}将删除标签 {tag} (digest: {digest})")
        return True

    # 发送删除请求
    delete_url = f"https://{registry}/v2/{namespace}/manifests/{digest}"
    headers = {
        "Docker-Distribution-Api-Version": "registry/2.0",
        "Authorization": f"Bearer {delete_token}",
    }

    logger.info(f"发送删除请求: {delete_url}")
    response = httpx.delete(delete_url, headers=headers)

    if response.status_code in [200, 202]:
        logger.info(f"成功删除标签: {tag}")
        return True
    elif response.status_code == 401:
        logger.error(f"删除失败 {tag}: HTTP 401 - 权限不足")
        logger.error("可能的原因:")
        logger.error("  1. 当前账号没有删除镜像的权限")
        logger.error("  2. 需要在阿里云控制台开通 API 删除权限")
        logger.error("  3. 需要在 RAM 中配置容器镜像服务的删除权限")
        logger.error("\n解决建议:")
        logger.error("  - 方案1: 联系阿里云客服或提交工单申请删除权限")
        logger.error("  - 方案2: 使用阿里云控制台手动删除")
        logger.error("  - 方案3: 使用浏览器自动化（参考 浏览器删除方案.md）")
        logger.error(f"\n账号: {Config.get_username()}")
        logger.error(f"命名空间: {namespace}")
        logger.error(f"标签: {tag}")
        return False
    elif response.status_code == 404:
        logger.warning(f"标签不存在: {tag}")
        return False
    else:
        logger.error(f"删除失败 {tag}: HTTP {response.status_code}")
        logger.error(f"响应内容: {response.text}")
        return False
