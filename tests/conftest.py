"""Pytest 配置和共享 Fixture"""
import os
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_data_file() -> Path:
    """获取数据文件路径"""
    return Path(__file__).parent.parent / "data" / "images-beijing.txt"


@pytest.fixture
def sample_tags(mock_data_file: Path) -> List[str]:
    """从数据文件读取示例标签列表"""
    tags = []
    with open(mock_data_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                # 提取 tag 部分，格式：registry:port/namespace/repo:tag
                if ':' in line:
                    tag = line.rsplit(':', 1)[-1]
                    tags.append(tag)
    return tags


@pytest.fixture
def sample_images(mock_data_file: Path) -> List[str]:
    """从数据文件读取示例镜像列表"""
    images = []
    with open(mock_data_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                images.append(line)
    return images


@pytest.fixture
def mock_env_vars():
    """Mock 环境变量"""
    with patch.dict(os.environ, {
        'ALIYUN_REGISTRY': 'registry.cn-beijing.aliyuncs.com',
        'ALIYUN_NAME_SPACE': 'winwin',
        'ALIYUN_REGISTRY_USER': 'test_user',
        'ALIYUN_REGISTRY_PASSWORD': 'test_password'
    }):
        yield


@pytest.fixture
def mock_http_response():
    """Mock HTTP 响应"""
    def _mock_response(status_code: int, json_data: dict = None, headers: dict = None):
        mock = Mock()
        mock.status_code = status_code
        mock.json.return_value = json_data or {}
        mock.headers = headers or {}
        mock.text = ""
        return mock
    return _mock_response
