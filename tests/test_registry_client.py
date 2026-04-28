"""测试 Registry 标签查询功能"""

from unittest.mock import Mock, patch

from src.winwin_image_mirror.registry.tags import get_image_tags


class TestGetImageTags:
    """测试 get_image_tags 函数"""

    @patch("src.winwin_image_mirror.registry.tags.httpx.get")
    def test_get_image_tags_success(self, mock_tags_get, mock_env_vars):
        """测试成功获取标签"""
        auth_response_401 = Mock()
        auth_response_401.status_code = 401
        auth_response_401.headers = {
            "Www-Authenticate": 'realm="https://auth.example.com",service="registry",scope="repository:winwin:pull"'
        }

        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {"token": "test-token"}

        tags_response = Mock()
        tags_response.status_code = 200
        tags_response.json.return_value = {"tags": ["tag1", "tag2"]}

        mock_tags_get.side_effect = [auth_response_401, token_response, tags_response]

        tags = get_image_tags()
        assert tags == ["tag1", "tag2"]

    @patch("src.winwin_image_mirror.registry.tags.httpx.get")
    def test_get_image_tags_auth_error(self, mock_get, mock_env_vars):
        """测试认证错误"""
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
