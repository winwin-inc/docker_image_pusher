"""测试 Registry 客户端模块"""
import pytest
from unittest.mock import Mock, patch
from src.registry.tags import get_image_tags, delete_image_tag


class TestGetImageTags:
    """测试 get_image_tags 函数"""

    @patch('src.registry.tags.httpx.get')
    def test_get_image_tags_success(self, mock_tags_get, mock_env_vars):
        """测试成功获取标签"""
        # 设置 auth 模块的 get 调用
        auth_response_401 = Mock()
        auth_response_401.status_code = 401
        auth_response_401.headers = {
            'Www-Authenticate': 'realm="https://auth.example.com",service="registry",scope="repository:winwin:pull"'
        }

        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {"token": "test-token"}

        # 设置 tags 模块的 get 调用
        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.json.return_value = {"tags": ["tag1", "tag2"]}

        mock_tags_get.side_effect = [auth_response_401, token_response, tags_response]

        tags = get_image_tags()
        assert tags == ["tag1", "tag2"]

    @patch('src.registry.tags.httpx.get')
    def test_get_image_tags_auth_error(self, mock_get, mock_env_vars):
        """测试认证错误"""
        # Mock 认证请求失败
        response = Mock()
        response.status_code = 500
        mock_get.return_value = response

        tags = get_image_tags()
        assert tags == []

    def test_get_image_tags_missing_env(self):
        """测试缺少环境变量"""
        import os
        with patch.dict(os.environ, {}, clear=True):
            tags = get_image_tags()
            assert tags == []


class TestDeleteImageTag:
    """测试 delete_image_tag 函数"""

    @patch('src.registry.tags.httpx.delete')
    @patch('src.registry.tags.get_auth_token')
    @patch('src.registry.tags.httpx.get')
    def test_delete_tag_success(self, mock_tags_get, mock_get_auth_token, mock_delete, mock_env_vars):
        """测试成功删除标签"""
        # Mock get_auth_token 直接返回 token
        mock_get_auth_token.return_value = "test-token"

        # Mock tags 模块的 get 调用（获取 manifest）
        digest_response = Mock()
        digest_response.status_code = 200
        digest_response.headers = {"Docker-Content-Digest": "sha256:abc123"}
        mock_tags_get.return_value = digest_response

        # Mock 删除
        delete_response = Mock()
        delete_response.status_code = 202
        mock_delete.return_value = delete_response

        success = delete_image_tag("test-tag")
        assert success is True

    @patch('src.registry.tags.httpx.delete')
    @patch('src.registry.tags.get_auth_token')
    @patch('src.registry.tags.httpx.get')
    def test_delete_tag_dry_run(self, mock_tags_get, mock_get_auth_token, mock_delete, mock_env_vars):
        """测试删除标签 - dry-run 模式"""
        # Mock get_auth_token 直接返回 token
        mock_get_auth_token.return_value = "test-token"

        # Mock digest 获取
        digest_response = Mock()
        digest_response.status_code = 200
        digest_response.headers = {"Docker-Content-Digest": "sha256:abc123"}
        mock_tags_get.return_value = digest_response

        success = delete_image_tag("test-tag", dry_run=True)
        assert success is True
        # 验证没有调用删除 API
        mock_delete.assert_not_called()

    @patch('src.registry.tags.get_auth_token')
    @patch('src.registry.tags.httpx.get')
    def test_delete_tag_not_found(self, mock_tags_get, mock_get_auth_token, mock_env_vars):
        """测试删除不存在的标签"""
        # Mock get_auth_token 直接返回 token
        mock_get_auth_token.return_value = "test-token"

        # Mock digest 获取返回 404
        digest_response = Mock()
        digest_response.status_code = 404
        mock_tags_get.return_value = digest_response

        success = delete_image_tag("non-existent-tag")
        assert success is False

    @patch('src.registry.tags.httpx.delete')
    @patch('src.registry.tags.get_auth_token')
    @patch('src.registry.tags.httpx.get')
    def test_delete_tag_permission_denied(self, mock_tags_get, mock_get_auth_token, mock_delete, mock_env_vars):
        """测试删除权限不足"""
        # Mock get_auth_token 直接返回 token
        mock_get_auth_token.return_value = "test-token"

        # Mock digest 获取
        digest_response = Mock()
        digest_response.status_code = 200
        digest_response.headers = {"Docker-Content-Digest": "sha256:abc123"}
        mock_tags_get.return_value = digest_response

        # Mock 删除返回 401（权限不足）
        delete_response = Mock()
        delete_response.status_code = 401
        mock_delete.return_value = delete_response

        success = delete_image_tag("test-tag")
        assert success is False
