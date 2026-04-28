"""Registry API 客户端

封装 Docker Registry API 操作。
"""
from typing import List, Optional

from ..core.config import Config
from .tags import get_image_tags, delete_image_tag


class RegistryClient:
    """Docker Registry API 客户端

    提供简化的接口来访问 Docker Registry API。
    """

    def __init__(self):
        """初始化 Registry 客户端

        验证环境变量配置。
        """
        Config.validate()

    def get_tags(self) -> List[str]:
        """获取所有镜像标签

        Returns:
            镜像标签列表
        """
        return get_image_tags()

    def delete_tag(self, tag: str, dry_run: bool = False) -> bool:
        """删除指定的镜像标签

        Args:
            tag: 要删除的标签
            dry_run: 预览模式，不实际删除

        Returns:
            是否删除成功
        """
        return delete_image_tag(tag, dry_run=dry_run)
