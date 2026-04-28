"""Tag 操作模块

提供 Docker Registry API 的 Tag 列表查询功能。
"""

import base64
import logging
import re
from typing import List, Optional
from urllib.parse import urlencode

import httpx

from ..core.config import Config

logger = logging.getLogger(__name__)


def _get_auth_token(scope_type: str = "pull") -> Optional[str]:
    """获取 Docker Registry API 认证 token"""
    try:
        namespace = Config.get_namespace()
        registry = Config.get_registry()
        username = Config.get_username()
        password = Config.get_password()
    except KeyError as e:
        logger.error(f"缺少环境变量: {e}")
        return None

    url = f"https://{registry}/v2/{namespace}/tags/list"
    response = httpx.get(url)

    if response.status_code != 401:
        return None

    auth_header = response.headers.get("Www-Authenticate")
    match = re.search(r'realm="([^"]+)",service="([^"]+)",scope="([^"]+)"', auth_header)
    if not match:
        return None

    realm, service, _ = match.groups()
    # scope 格式: repository:{namespace}:{action}，namespace 已包含 repo 名（如 "winwin/tool"）
    scope = f"repository:{namespace}:{scope_type}"

    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    token_url = f"{realm}?" + urlencode({"service": service, "scope": scope})
    headers = {"Authorization": f"Basic {encoded_credentials}"}

    token_response = httpx.get(token_url, headers=headers)
    if token_response.status_code == 200:
        return token_response.json().get("token")
    return None


def get_image_tags() -> List[str]:
    """获取镜像标签列表"""
    token = _get_auth_token("pull")
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
        return response.json()["tags"]
    logger.error(f"请求失败，状态码: {response.status_code}")
    return []


def delete_tag(tag: str) -> str:
    """通过 Registry API 删除指定镜像标签

    Args:
        tag: 要删除的标签名称

    Returns:
        "deleted": 成功删除
        "not_found": 标签不存在
        "error": 删除失败
    """
    # 需要 push 权限才能删除
    token = _get_auth_token("*")
    if not token:
        logger.error("无法获取认证 token，请检查阿里云凭证是否正确")
        return "error"

    try:
        namespace = Config.get_namespace()
        registry = Config.get_registry()
    except KeyError as e:
        logger.error(f"缺少环境变量: {e}")
        return "error"

    # 获取 tag 的 digest（尝试 v2 和 v1 两种 manifest schema）
    manifest_url = f"https://{registry}/v2/{namespace}/manifests/{tag}"
    for accept in [
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.v1+json",
    ]:
        head_resp = httpx.head(
            manifest_url,
            headers={"Authorization": f"Bearer {token}", "Accept": accept},
            timeout=30,
        )
        if head_resp.status_code == 200:
            break
    else:
        # 所有 schema 都返回 404，说明 tag 不存在
        if head_resp.status_code == 404:
            logger.info(f"tag '{tag}' 不存在（已删除或从未推送）")
            return "not_found"
        logger.error(f"获取 tag '{tag}' 的 digest 失败，状态码: {head_resp.status_code}")
        return "error"

    digest = head_resp.headers.get("Docker-Content-Digest")
    if not digest:
        logger.error(f"tag '{tag}' 响应中无 Docker-Content-Digest")
        return "error"

    # 删除 manifest
    delete_url = f"https://{registry}/v2/{namespace}/manifests/{digest}"
    del_resp = httpx.delete(
        delete_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if del_resp.status_code in (202, 204):
        logger.info(f"✓ 删除成功: {tag}")
        return "deleted"
    else:
        logger.error(
            f"删除 tag '{tag}' 失败，状态码: {del_resp.status_code}, 响应: {del_resp.text[:200]}"
        )
        return "error"
