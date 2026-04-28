#!/usr/bin/env python3
"""
Playwright 元素选择器助手

帮助您找到正确的 CSS 选择器来定位页面元素
"""

import os

# 加载环境变量
if os.path.exists(".env.beijing"):
    with open(".env.beijing") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key.strip()] = value.strip()

from playwright.sync_api import sync_playwright


def main():
    print("=" * 60)
    print("Playwright 元素选择器助手")
    print("=" * 60)
    print()

    # 构建目标 URL
    registry = os.getenv("ALIYUN_REGISTRY", "registry.cn-beijing.aliyuncs.com")
    namespace = os.getenv("ALIYUN_NAME_SPACE", "winwin/tool")
    region = registry.replace("registry.", "").replace(".aliyuncs.com", "")
    url = f"https://cr.console.aliyun.com/repository/{region}/{namespace}/images"

    print(f"目标页面: {url}")
    print(f"Registry: {registry}")
    print(f"Namespace: {namespace}")
    print()
    print("启动浏览器...")
    print()
    print("📌 使用提示:")
    print("1. 浏览器会打开并导航到目标页面")
    print("2. 在浏览器中手动登录(如需要)")
    print("3. 找到您想删除的 tag 元素")
    print("4. 在浏览器控制台 (F12) 运行以下代码来获取选择器:")
    print()
    print("   // 获取元素的选择器")
    print("   const element = document.querySelector('您的tag元素');")
    print("   console.log(element);")
    print()
    print("5. 按回车键关闭浏览器")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle")

            print("✅ 页面加载完成!")
            print()
            print("💡 提示: 按 Ctrl+Shift+C 打开开发者工具查看元素")
            print("💡 提示: 按 Ctrl+Shift+I 查看页面源代码")
            print()
            input("按回车键关闭浏览器...")

        finally:
            browser.close()

    print()
    print("浏览器已关闭")


if __name__ == "__main__":
    main()
