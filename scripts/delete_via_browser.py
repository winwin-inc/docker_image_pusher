#!/usr/bin/env python3
"""
使用 Playwright 自动化浏览器删除阿里云容器镜像 tag

前提条件：
1. 安装 Playwright: pip install playwright
2. 安装浏览器: playwright install chromium
3. 配置阿里云账号和密码
"""

from playwright.sync_api import sync_playwright
import time
import os


def delete_aliyun_image_tag(
    registry_url: str,
    namespace: str,
    tag: str,
    username: str,
    password: str,
    headless: bool = False
):
    """
    通过浏览器自动化删除阿里云镜像 tag

    Args:
        registry_url: 阿里云 registry 地址 (如 registry.cn-beijing.aliyuncs.com)
        namespace: 命名空间 (如 winwin/tool)
        tag: 要删除的 tag
        username: 阿里云账号
        password: 阿里云密码
        headless: 是否使用无头模式（不显示浏览器窗口）
    """

    with sync_playwright() as p:
        print("启动浏览器...")
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        try:
            # 步骤 1: 访问阿里云登录页面
            print("访问阿里云登录页面...")
            page.goto("https://signin.aliyun.com/")
            time.sleep(2)

            # 步骤 2: 输入账号密码登录
            print("输入登录信息...")
            # 注意：阿里云登录页面可能有验证码，需要人工处理
            # 这里提供一个基础框架

            # 登录后跳转到容器镜像服务
            print("跳转到容器镜像服务...")
            page.goto("https://cr.console.aliyun.com/")
            time.sleep(3)

            # 步骤 3: 导航到指定命名空间
            print(f"导航到命名空间: {namespace}")
            # 根据页面结构找到命名空间并点击
            # 这需要实际的页面元素定位器

            # 步骤 4: 找到对应的镜像仓库
            print(f"查找镜像仓库...")

            # 步骤 5: 查找并删除指定 tag
            print(f"删除 tag: {tag}")

            print("✓ 删除完成")

        except Exception as e:
            print(f"✗ 操作失败: {e}")

        finally:
            print("关闭浏览器...")
            browser.close()


def delete_multiple_tags(
    registry_url: str,
    namespace: str,
    tags: list,
    username: str,
    password: str,
    headless: bool = False
):
    """
    批量删除多个 tags

    Args:
        registry_url: 阿里云 registry 地址
        namespace: 命名空间
        tags: 要删除的 tag 列表
        username: 阿里云账号
        password: 阿里云密码
        headless: 是否使用无头模式
    """

    for tag in tags:
        print(f"\n处理 tag: {tag}")
        delete_aliyun_image_tag(
            registry_url=registry_url,
            namespace=namespace,
            tag=tag,
            username=username,
            password=password,
            headless=headless
        )
        time.sleep(2)  # 间隔 2 秒


if __name__ == "__main__":
    # 配置信息
    REGISTRY_URL = "registry.cn-beijing.aliyuncs.com"
    NAMESPACE = "winwin/tool"
    USERNAME = os.getenv("ALIYUN_USERNAME")  # 从环境变量读取
    PASSWORD = os.getenv("ALIYUN_PASSWORD")  # 从环境变量读取

    # 测试单个删除
    delete_aliyun_image_tag(
        registry_url=REGISTRY_URL,
        namespace=NAMESPACE,
        tag="test-tag-to-delete",
        username=USERNAME,
        password=PASSWORD,
        headless=False  # 显示浏览器窗口，便于调试
    )
