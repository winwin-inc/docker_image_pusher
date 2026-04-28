"""测试配置管理模块"""
import os
import pytest
from unittest.mock import patch

from src.core.config import Config
from src.core.exceptions import ConfigError


class TestConfig:
    """测试 Config 类"""

    def test_get_registry(self, mock_env_vars):
        """测试获取 Registry 地址"""
        registry = Config.get_registry()
        assert registry == 'registry.cn-beijing.aliyuncs.com'

    def test_get_namespace(self, mock_env_vars):
        """测试获取命名空间"""
        namespace = Config.get_namespace()
        assert namespace == 'winwin'

    def test_get_username(self, mock_env_vars):
        """测试获取用户名"""
        username = Config.get_username()
        assert username == 'test_user'

    def test_get_password(self, mock_env_vars):
        """测试获取密码"""
        password = Config.get_password()
        assert password == 'test_password'

    def test_validate_success(self, mock_env_vars):
        """测试验证成功"""
        assert Config.validate() is True

    def test_validate_missing_env_var(self):
        """测试验证失败 - 缺少环境变量"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError, match="缺少必需的环境变量"):
                Config.validate()

    def test_get_registry_missing_env(self):
        """测试获取 Registry - 缺少环境变量"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyError):
                Config.get_registry()
