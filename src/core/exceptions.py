"""自定义异常类

定义项目中使用的所有自定义异常。
"""


class DockerImagePusherError(Exception):
    """基础异常类

    所有项目自定义异常的基类。
    """
    pass


class RegistryError(DockerImagePusherError):
    """Registry API 错误

    当与 Docker Registry API 交互时发生错误。
    """
    pass


class AuthError(DockerImagePusherError):
    """认证错误

    当认证失败或获取 token 失败时抛出。
    """
    pass


class ImageError(DockerImagePusherError):
    """镜像操作错误

    当镜像解析、推送等操作失败时抛出。
    """
    pass


class BrowserError(DockerImagePusherError):
    """浏览器自动化错误

    当浏览器自动化操作失败时抛出。
    """
    pass


class ConfigError(DockerImagePusherError):
    """配置错误

    当配置缺失或无效时抛出。
    """
    pass
