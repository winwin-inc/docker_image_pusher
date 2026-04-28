"""镜像名称解析模块

提供镜像名称解析和标签生成功能。
"""


def parse_image(image_name: str) -> dict:
    """解析镜像名称

    Args:
        image_name: 镜像名称，如 "nginx", "nginx:latest", "library/nginx:latest"

    Returns:
        包含镜像信息的字典:
        {
            "name": str,       # 原始镜像名称
            "registry": str,   # registry 地址
            "namespace": str,  # 命名空间
            "repository": str, # 仓库名
            "tag": str | None, # 标签
        }
    """
    if ":" in image_name:
        prefix, tag = image_name.rsplit(":", 1)
    else:
        prefix = image_name
        tag = None

    parts = prefix.split("/")
    if len(parts) == 1:
        registry = "docker.io"
        namespace = "library"
        name = parts[0]
    elif len(parts) == 2:
        registry = "docker.io"
        namespace = parts[0]
        name = parts[1]
    elif len(parts) == 3:
        registry = parts[0]
        namespace = parts[1]
        name = parts[2]
    else:
        # 更复杂的路径，取最后三个部分
        registry = parts[-3]
        namespace = parts[-2]
        name = parts[-1]

    return {
        "name": image_name,
        "registry": registry,
        "namespace": namespace,
        "repository": name,
        "tag": tag if ":" in image_name else None,
    }


def get_image_tag(image: dict) -> list:
    """生成镜像标签的各种变体格式

    Args:
        image: 镜像信息字典（由 parse_image 返回）

    Returns:
        镜像标签变体列表
    """
    if image["tag"]:
        name = f"{image['repository']}-{image['tag']}"
    else:
        name = image["repository"]

    if image["namespace"] == "bitnami":
        name = f"{image['namespace']}-{name}"

    names = []
    if image.get("alias"):
        names.append(image["alias"] + "-" + image["tag"])

    return names + [
        name,
        f"{image['namespace']}-{name}",
        f"{image['registry']}-{image['namespace']}-{name}",
    ]
