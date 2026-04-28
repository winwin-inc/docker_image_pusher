"""测试镜像解析模块"""
import pytest

from src.image.parser import parse_image, get_image_tag


class TestParseImage:
    """测试 parse_image 函数"""

    def test_parse_simple_image(self):
        """测试解析简单镜像名称"""
        result = parse_image("nginx")
        assert result["name"] == "nginx"
        assert result["registry"] == "docker.io"
        assert result["namespace"] == "library"
        assert result["repository"] == "nginx"
        assert result["tag"] is None

    def test_parse_image_with_tag(self):
        """测试解析带标签的镜像"""
        result = parse_image("nginx:latest")
        assert result["name"] == "nginx:latest"
        assert result["registry"] == "docker.io"
        assert result["namespace"] == "library"
        assert result["repository"] == "nginx"
        assert result["tag"] == "latest"

    def test_parse_namespaced_image(self):
        """测试解析带命名空间的镜像"""
        result = parse_image("bitnami/nginx")
        assert result["name"] == "bitnami/nginx"
        assert result["registry"] == "docker.io"
        assert result["namespace"] == "bitnami"
        assert result["repository"] == "nginx"
        assert result["tag"] is None

    def test_parse_full_image(self):
        """测试解析完整路径的镜像"""
        result = parse_image("registry.cn-beijing.aliyuncs.com/winwin/tool:tag123")
        assert result["name"] == "registry.cn-beijing.aliyuncs.com/winwin/tool:tag123"
        assert result["registry"] == "registry.cn-beijing.aliyuncs.com"
        assert result["namespace"] == "winwin"
        assert result["repository"] == "tool"
        assert result["tag"] == "tag123"

    def test_parse_bitnami_image_with_tag(self):
        """测试解析 bitnami 镜像（特殊处理）"""
        result = parse_image("bitnami/nginx:1.21")
        assert result["name"] == "bitnami/nginx:1.21"
        assert result["namespace"] == "bitnami"
        assert result["repository"] == "nginx"
        assert result["tag"] == "1.21"


class TestGetImageTag:
    """测试 get_image_tag 函数"""

    def test_get_image_tag_without_tag(self):
        """测试获取无标签镜像的 tag 列表"""
        image = parse_image("nginx")
        tags = get_image_tag(image)
        assert "nginx" in tags
        assert "library-nginx" in tags
        assert "docker.io-library-nginx" in tags

    def test_get_image_tag_with_tag(self):
        """测试获取带标签镜像的 tag 列表"""
        image = parse_image("nginx:latest")
        tags = get_image_tag(image)
        assert "nginx-latest" in tags
        assert "library-nginx-latest" in tags
        assert "docker.io-library-nginx-latest" in tags

    def test_get_image_tag_bitnami(self):
        """测试 bitnami 镜像的 tag 生成（特殊规则）"""
        image = parse_image("bitnami/nginx:latest")
        tags = get_image_tag(image)
        # bitnami 镜像会添加额外的前缀
        assert any("bitnami" in tag for tag in tags)
        # name 会是 "bitnami-nginx-latest"
        assert "bitnami-nginx-latest" in tags

    def test_get_image_tag_with_alias(self):
        """测试带别名的镜像"""
        image = parse_image("nginx:latest")
        image["alias"] = "web-server"
        tags = get_image_tag(image)
        assert "web-server-latest" in tags
        assert "nginx-latest" in tags
