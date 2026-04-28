#!/usr/bin/env python3
"""
快捷录制脚本 - 录制删除 tag 的操作

使用方法:
    1. 运行此脚本
    2. 在浏览器中执行删除操作
    3. 按 Ctrl+C 停止录制
    4. 查看生成的代码
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
    print("Playwright 操作录制")
    print("=" * 60)
    print()

    # 构建目标 URL
    registry = os.getenv("ALIYUN_REGISTRY", "registry.cn-beijing.aliyuncs.com")
    namespace = os.getenv("ALIYUN_NAME_SPACE", "winwin/tool")
    region = registry.replace("registry.", "").replace(".aliyuncs.com", "")
    url = f"https://cr.console.aliyun.com/repository/{region}/{namespace}/images"

    print("📹 将录制以下页面的操作:")
    print(f"   URL: {url}")
    print()
    print("📋 录制步骤:")
    print("   1. 浏览器会自动打开")
    print("   2. 如果需要登录,请先登录")
    print("   3. 找到您想删除的 tag")
    print("   4. 点击删除按钮")
    print("   5. 确认删除")
    print("   6. 按 Ctrl+C 停止录制")
    print()
    print("💡 生成的代码会保存到: recorded_delete.py")
    print("=" * 60)
    print()

    # 检查是否已有登录状态
    use_saved_state = os.path.exists("aliyun_state.json")
    if use_saved_state:
        print("✅ 检测到已保存的登录状态,将使用该状态")

    output_file = "recorded_delete.py"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500,  # 减慢操作,方便查看
        )

        # 使用保存的登录状态(如果存在)
        if use_saved_state:
            context = browser.new_context(
                storage_state="aliyun_state.json", viewport={"width": 1920, "height": 1080}
            )
        else:
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

        page = context.new_page()

        try:
            print(f"🌐 正在打开页面: {url}")
            page.goto(url, wait_until="networkidle")
            print("✅ 页面加载完成")
            print()
            print("🎬 现在开始执行您的删除操作...")
            print("⏹️  完成后按 Ctrl+C 停止录制")
            print("-" * 60)

            # 等待用户操作
            input("按回车键开始录制...")

            # 开始录制 - 这只是一个占位符
            # 实际录制需要使用 Playwright CLI
            print()
            print("⚠️  注意: 请使用以下命令进行完整录制:")
            print()
            print(f"   uv run playwright codegen {url} -o {output_file}")
            print()
            print("或在浏览器中打开开发者工具,手动记录选择器")
            input("按回车键关闭浏览器...")

        except KeyboardInterrupt:
            print()
            print("⏹️  录制已停止")
        finally:
            browser.close()

    print()
    print("=" * 60)
    print("💡 使用提示:")
    print()
    print("1. 查看页面元素:")
    print("   - 按 F12 打开开发者工具")
    print("   - 点击左上角的元素选择器(箭头图标)")
    print("   - 点击页面上的元素")
    print("   - 查看 HTML 源码,找到 class、id 等属性")
    print()
    print("2. 测试选择器:")
    print("   - 在控制台输入: document.querySelector('your-selector')")
    print("   - 或: document.querySelectorAll('your-selector')")
    print()
    print("3. 更新代码:")
    print(
        "   - 将选择器添加到 src/winwin_image_mirror/browser/deleter.py 的 _locate_tag_element 方法"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
