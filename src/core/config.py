"""配置管理模块

提供统一的配置访问接口，管理环境变量。
"""
import os
from typing import Optional


class Config:
    """配置管理类

    从环境变量读取阿里云容器镜像服务的配置信息。
    """

    @staticmethod
    def get_registry() -> str:
        """获取 Registry 地址

        Returns:
            str: 阿里云 Registry 地址

        Raises:
            KeyError: 当环境变量 ALIYUN_REGISTRY 未设置时
        """
        return os.environ['ALIYUN_REGISTRY']

    @staticmethod
    def get_namespace() -> str:
        """获取命名空间

        Returns:
            str: 阿里云命名空间

        Raises:
            KeyError: 当环境变量 ALIYUN_NAME_SPACE 未设置时
        """
        return os.environ['ALIYUN_NAME_SPACE']

    @staticmethod
    def get_username() -> str:
        """获取用户名

        Returns:
            str: Registry 用户名

        Raises:
            KeyError: 当环境变量 ALIYUN_REGISTRY_USER 未设置时
        """
        return os.environ['ALIYUN_REGISTRY_USER']

    @staticmethod
    def get_password() -> str:
        """获取密码

        Returns:
            str: Registry 密码

        Raises:
            KeyError: 当环境变量 ALIYUN_REGISTRY_PASSWORD 未设置时
        """
        return os.environ['ALIYUN_REGISTRY_PASSWORD']

    @staticmethod
    def validate() -> bool:
        """验证所有必需的环境变量是否已设置

        Returns:
            bool: 如果所有必需的环境变量都已设置则返回 True

        Raises:
            KeyError: 当有必需的环境变量未设置时
        """
        required_vars = [
            'ALIYUN_REGISTRY',
            'ALIYUN_NAME_SPACE',
            'ALIYUN_REGISTRY_USER',
            'ALIYUN_REGISTRY_PASSWORD'
        ]

        missing_vars = [var for var in required_vars if var not in os.environ]

        if missing_vars:
            raise KeyError(f"缺少必需的环境变量: {', '.join(missing_vars)}")

        return True
