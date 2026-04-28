"""认证模块

提供 Docker Registry API 认证功能。
"""
import base64
import logging
import re
from typing import Optional
from urllib.parse import urlencode

import httpx

from ..core.config import Config

logger = logging.getLogger(__name__)


def get_auth_token(scope_type: str = "pull", namespace: Optional[str] = None) -> Optional[str]:
    """获取 Docker Registry API 认证 token

    Args:
        scope_type: 权限类型 ("pull", "delete")
        namespace: 命名空间，默认使用环境变量 ALIYUN_NAME_SPACE

    Returns:
        Bearer token 或 None
    """
    try:
        namespace = namespace or Config.get_namespace()
        registry = Config.get_registry()
    except KeyError as e:
        logger.error(f"缺少环境变量: {e}")
        return None

    # 发起初始请求获取认证信息
    url = f"https://{registry}/v2/{namespace}/tags/list"
    response = httpx.get(url)

    if response.status_code != 401:
        logger.error(f"期望 401 响应，实际: {response.status_code}")
        return None

    # 解析 Www-Authenticate 头
    auth_header = response.headers.get("Www-Authenticate")
    match = re.search(r'realm="([^"]+)",service="([^"]+)",scope="([^"]+)"', auth_header)

    if not match:
        logger.error("无法解析 Www-Authenticate 头")
        return None

    realm, service, _ = match.groups()

    # 根据 scope_type 设置权限
    if scope_type == "delete":
        scope = f"repository:{namespace}:delete"
    else:
        scope = f"repository:{namespace}:pull"

    # Basic Auth
    credentials = f"{Config.get_username()}:{Config.get_password()}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # 请求 Token
    token_url = f"{realm}?" + urlencode({"service": service, "scope": scope})
    headers = {"Authorization": f"Basic {encoded_credentials}"}

    logger.debug(f"请求 Token ({scope_type}): {token_url}")
    token_response = httpx.get(token_url, headers=headers)

    if token_response.status_code == 200:
        token = token_response.json().get("token")
        logger.debug(f"获取到 Token: {token[:20]}...")
        return token
    else:
        logger.error(f"获取 Token 失败: {token_response.status_code}")
        return None
