#!/usr/bin/env python3
"""
浏览器删除模块的单元测试
"""

import json
import os
import tempfile

import pytest

from src.winwin_image_mirror.browser.deleter import AliyunBrowserDeleter
from src.winwin_image_mirror.browser.state import verify_login_state


class TestVerifyLoginState:
    """测试登录状态验证功能"""

    def test_verify_login_state_not_exists(self):
        """测试:登录状态文件不存在"""
        result = verify_login_state("non_existent_file.json")
        assert result is False

    def test_verify_login_state_invalid_json(self):
        """测试:登录状态文件不是有效的JSON"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            f.write("invalid json content")
            f.flush()
            temp_path = f.name

        try:
            result = verify_login_state(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_verify_login_state_no_cookies(self):
        """测试:登录状态文件中没有cookies"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"origins": []}, f)
            f.flush()
            temp_path = f.name

        try:
            result = verify_login_state(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_verify_login_state_empty_cookies(self):
        """测试:登录状态文件中cookies为空列表"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"cookies": []}, f)
            f.flush()
            temp_path = f.name

        try:
            result = verify_login_state(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_verify_login_state_valid(self):
        """测试:有效的登录状态文件"""
        import time

        current_time = int(time.time())

        valid_state = {
            "cookies": [
                {
                    "name": "test_cookie",
                    "value": "test_value",
                    "expires": current_time + 3600,  # 1小时后过期
                    "domain": ".aliyun.com",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(valid_state, f)
            f.flush()
            temp_path = f.name

        try:
            result = verify_login_state(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_verify_login_state_expired(self):
        """测试:登录状态文件中的cookies已过期"""
        import time

        past_time = int(time.time()) - 3600  # 1小时前过期

        expired_state = {
            "cookies": [
                {
                    "name": "test_cookie",
                    "value": "test_value",
                    "expires": past_time,
                    "domain": ".aliyun.com",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(expired_state, f)
            f.flush()
            temp_path = f.name

        try:
            result = verify_login_state(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_verify_login_state_session_cookie(self):
        """测试:会话cookie(expires=-1)不会过期"""
        session_state = {
            "cookies": [
                {
                    "name": "session_cookie",
                    "value": "session_value",
                    "expires": -1,  # 会话cookie
                    "domain": ".aliyun.com",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(session_state, f)
            f.flush()
            temp_path = f.name

        try:
            result = verify_login_state(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)


class TestAliyunBrowserDeleterInit:
    """测试 AliyunBrowserDeleter 初始化"""

    def test_init_missing_env_vars(self):
        """测试:缺少环境变量时抛出异常"""
        # 临时保存环境变量
        old_registry = os.environ.get("ALIYUN_REGISTRY")
        old_namespace = os.environ.get("ALIYUN_NAME_SPACE")

        try:
            # 删除环境变量
            if "ALIYUN_REGISTRY" in os.environ:
                del os.environ["ALIYUN_REGISTRY"]
            if "ALIYUN_NAME_SPACE" in os.environ:
                del os.environ["ALIYUN_NAME_SPACE"]

            # 应该抛出 KeyError
            with pytest.raises(KeyError):
                AliyunBrowserDeleter()

        finally:
            # 恢复环境变量
            if old_registry:
                os.environ["ALIYUN_REGISTRY"] = old_registry
            if old_namespace:
                os.environ["ALIYUN_NAME_SPACE"] = old_namespace

    def test_build_console_url_beijing(self):
        """测试:从registry URL构建控制台URL(北京)"""
        old_registry = os.environ.get("ALIYUN_REGISTRY")
        old_namespace = os.environ.get("ALIYUN_NAME_SPACE")

        try:
            os.environ["ALIYUN_REGISTRY"] = "registry.cn-beijing.aliyuncs.com"
            os.environ["ALIYUN_NAME_SPACE"] = "test/repo"

            deleter = AliyunBrowserDeleter()
            # 新实现返回 https://cr.{region}.aliyuncs.com/rep/{namespace}
            assert deleter.base_url == "https://cr.cn-beijing.aliyuncs.com/rep/test/repo"

        finally:
            if old_registry:
                os.environ["ALIYUN_REGISTRY"] = old_registry
            if old_namespace:
                os.environ["ALIYUN_NAME_SPACE"] = old_namespace

    def test_build_console_url_hangzhou(self):
        """测试:从registry URL构建控制台URL(杭州)"""
        old_registry = os.environ.get("ALIYUN_REGISTRY")
        old_namespace = os.environ.get("ALIYUN_NAME_SPACE")

        try:
            os.environ["ALIYUN_REGISTRY"] = "registry.cn-hangzhou.aliyuncs.com"
            os.environ["ALIYUN_NAME_SPACE"] = "test/repo"

            deleter = AliyunBrowserDeleter()
            # 新实现返回 https://cr.{region}.aliyuncs.com/rep/{namespace}
            assert deleter.base_url == "https://cr.cn-hangzhou.aliyuncs.com/rep/test/repo"

        finally:
            if old_registry:
                os.environ["ALIYUN_REGISTRY"] = old_registry
            if old_namespace:
                os.environ["ALIYUN_NAME_SPACE"] = old_namespace


@pytest.mark.integration
class TestBrowserDeleteIntegration:
    """
    浏览器删除集成测试(需要真实的阿里云环境)

    运行这些测试前需要:
    1. 设置环境变量 ALIYUN_REGISTRY 和 ALIYUN_NAME_SPACE
    2. 运行 cli.py delete-browser-login 保存登录状态
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """检查测试环境"""
        if not os.getenv("ALIYUN_REGISTRY"):
            pytest.skip("缺少 ALIYUN_REGISTRY 环境变量")

        if not os.getenv("ALIYUN_NAME_SPACE"):
            pytest.skip("缺少 ALIYUN_NAME_SPACE 环境变量")

        if not os.path.exists("aliyun_state.json"):
            pytest.skip("缺少登录状态文件,请先运行: uv run cli.py delete-browser-login")

    def test_connect_with_valid_state(self):
        """测试:使用有效登录状态连接浏览器"""
        with AliyunBrowserDeleter(headless=True) as deleter:
            assert deleter.browser is not None
            assert deleter.page is not None
            assert deleter.context is not None

    def test_connect_with_invalid_state(self):
        """测试:使用无效登录状态连接浏览器"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"cookies": []}, f)
            f.flush()
            temp_path = f.name

        try:
            deleter = AliyunBrowserDeleter(storage_state_path=temp_path)
            result = deleter.connect()
            assert result is False
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
