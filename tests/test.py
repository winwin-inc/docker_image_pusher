import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
import re
from os import environ as env
from urllib.parse import urlencode

import httpx
import logging
from util import setup_logging

setup_logging(log_level="DEBUG")

logger = logging.getLogger(__name__)


def test_get_image_tag():
    tags = get_image_tags("winwin/website")
    print(tags)


def get_auth_token(namespace, scope_type="pull"):
    """获取认证 token"""
    url = f"https://{env['ALIYUN_REGISTRY']}/v2/{namespace}/tags/list"
    response = httpx.get(url)

    if response.status_code == 401:
        # 解析 Www-Authenticate 字段
        auth_header = response.headers.get("Www-Authenticate")
        match = re.search(
            r'realm="([^"]+)",service="([^"]+)",scope="([^"]+)"', auth_header
        )
        if match:
            realm, service, scope = match.groups()
            # 修改 scope 以支持删除操作
            if scope_type == "delete":
                scope = f"repository:{namespace}:pull,push,delete"
            
            # 对用户名和密码进行 Base64 编码
            credentials = (
                f"{env['ALIYUN_REGISTRY_USER']}:{env['ALIYUN_REGISTRY_PASSWORD']}"
            )
            encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
                "utf-8"
            )
            # 设置请求头
            headers = {"Authorization": f"Basic {encoded_credentials}"}
            # 向认证服务请求 Token
            token_url = f"{realm}?" + urlencode({"service": service, "scope": scope})
            logger.debug(f"Token 请求 URL: {token_url}")
            token_response = httpx.get(token_url, headers=headers)
            if token_response.status_code == 200:
                logger.debug(f"Token 请求成功: {token_response.json()}")
                token = token_response.json().get("token")
                logger.debug(f"获取到的 Token: {token}")
                return token
            else:
                logger.error(f"获取 Token 失败，状态码: {token_response.status_code}")
        else:
            logger.error("无法解析 Www-Authenticate 头")
    return None


def get_image_tags(namespace):
    """获取镜像所有标签"""
    token = get_auth_token(namespace, "pull")
    if not token:
        return []
    
    url = f"https://{env['ALIYUN_REGISTRY']}/v2/{namespace}/tags/list"
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


def delete_image_tag(namespace, tag):
    """删除指定的镜像标签
    
    Args:
        namespace: 命名空间/仓库名称，例如 "winwin/website"
        tag: 要删除的标签
    """
    # 获取具有删除权限的 token
    token = get_auth_token(namespace, "delete")
    if not token:
        logger.error("获取 token 失败")
        return False
    
    # 第一步：获取镜像的 digest
    manifest_url = f"https://{env['ALIYUN_REGISTRY']}/v2/{namespace}/manifests/{tag}"
    headers = {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        "Docker-Distribution-Api-Version": "registry/2.0",
        "Authorization": f"Bearer {token}",
    }
    
    logger.info(f"获取镜像 manifest: {manifest_url}")
    response = httpx.get(manifest_url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"获取 manifest 失败，状态码: {response.status_code}")
        logger.error(f"响应内容: {response.text}")
        return False
    
    # 从响应头中获取 digest
    digest = response.headers.get("Docker-Content-Digest")
    if not digest:
        logger.error("无法获取 Docker-Content-Digest")
        return False
    
    logger.info(f"获取到 digest: {digest}")
    
    # 第二步：删除镜像
    delete_url = f"https://{env['ALIYUN_REGISTRY']}/v2/{namespace}/manifests/{digest}"
    headers = {
        "Docker-Distribution-Api-Version": "registry/2.0",
        "Authorization": f"Bearer {token}",
    }
    
    logger.info(f"发送删除请求: {delete_url}")
    response = httpx.delete(delete_url, headers=headers)
    
    if response.status_code in [200, 202]:
        logger.info(f"成功删除标签 {tag}")
        return True
    else:
        logger.error(f"删除失败，状态码: {response.status_code}")
        logger.error(f"响应内容: {response.text}")
        return False


def test_delete_tag():
    """测试删除标签功能"""
    namespace = "winwin/website"
    tag = 'v0.10.3'  # 修改为要删除的标签
    
    logger.info(f"准备删除 {namespace}:{tag}")
    result = delete_image_tag(namespace, tag)
    
    if result:
        logger.info("删除成功")
    else:
        logger.error("删除失败")
