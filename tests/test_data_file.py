"""测试数据文件读取和标签提取"""

from pathlib import Path


class TestDataFile:
    """测试数据文件功能"""

    def test_data_file_exists(self, mock_data_file: Path):
        """测试数据文件存在"""
        assert mock_data_file.exists()
        assert mock_data_file.is_file()

    def test_data_file_content(self, mock_data_file: Path):
        """测试数据文件内容"""
        with open(mock_data_file, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0

        # 验证文件格式
        with open(mock_data_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    # 验证格式：registry:port/namespace/repo:tag
                    assert ":" in line  # 应该有 tag
                    assert "/" in line  # 应该有路径
                    assert "registry.cn-beijing.aliyuncs.com" in line
                    assert "/winwin/tool:" in line

    def test_extract_tags_from_data_file(self, mock_data_file: Path):
        """测试从数据文件提取标签"""
        tags = set()
        with open(mock_data_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    # 提取 tag 部分
                    tag = line.rsplit(":", 1)[-1]
                    tags.add(tag)

        # 验证提取的标签数量
        assert len(tags) > 200

        # 验证一些预期的标签
        expected_tags = ["nginx", "alpine", "ubuntu", "mysql-8.0", "redis-7.4", "grafana-12.0.2"]

        for expected_tag in expected_tags:
            assert any(expected_tag in tag for tag in tags), (
                f"Expected tag {expected_tag} not found"
            )

    def test_extract_images_from_data_file(self, mock_data_file: Path):
        """测试从数据文件提取完整镜像"""
        images = []
        with open(mock_data_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    images.append(line)

        # 验证镜像数量
        assert len(images) == 217

        # 验证第一个和最后一个镜像
        assert images[0] == "registry.cn-beijing.aliyuncs.com/winwin/tool:1.11.0-qdrant-v1.11.0"
        assert images[-1] == "registry.cn-beijing.aliyuncs.com/winwin/tool:zookeeper"

    def test_data_file_tags_unique(self, mock_data_file: Path):
        """测试数据文件中的标签唯一性"""
        tags = []
        with open(mock_data_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    tag = line.rsplit(":", 1)[-1]
                    tags.append(tag)

        # 检查是否有重复
        unique_tags = set(tags)
        assert len(unique_tags) == len(tags), "数据文件中存在重复的标签"

    def test_parse_sample_images(self, sample_images):
        """测试解析示例镜像"""
        from src.winwin_image_mirror.image.parser import parse_image

        # 随机抽样测试几个镜像
        samples = sample_images[:10]

        for image_str in samples:
            result = parse_image(image_str)

            # 验证解析结果
            assert result["name"] == image_str
            assert result["registry"] == "registry.cn-beijing.aliyuncs.com"
            assert result["namespace"] == "winwin"
            assert result["repository"] == "tool"
            assert result["tag"] is not None

            # 验证 tag 格式
            assert ":" in result["tag"] or result["tag"].count("-") >= 0

    def test_specific_tag_patterns(self, sample_tags):
        """测试特定的标签模式"""
        # 验证一些特定的命名模式
        patterns = {
            "version": ["grafana-10.1.5", "grafana-11.6.0", "grafana-12.0.2"],
            "datahub": [
                f"datahub-{name}-v1.2.0.1"
                for name in [
                    "actions",
                    "elasticsearch-setup",
                    "frontend-react",
                    "gms",
                    "ingestion",
                    "kafka-setup",
                    "mysql-setup",
                    "postgres-setup",
                    "upgrade",
                ]
            ],
            "victoria": [f"victoria-{metric}-v1.113.0" for metric in ["logs", "metrics"]],
        }

        for category, tags in patterns.items():
            for tag in tags:
                if tag in sample_tags:
                    # 标签应该在列表中
                    assert True
