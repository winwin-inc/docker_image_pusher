"""浏览器登录状态管理

提供保存和验证浏览器登录状态的功能。
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


def save_login_state(storage_state_path: str) -> bool:
    """保存阿里云登录状态

    打开浏览器访问阿里云控制台，用户手动登录后保存状态。

    Args:
        storage_state_path: 登录状态保存路径

    Returns:
        是否成功保存登录状态
    """
    logger.info("正在打开浏览器...")
    logger.info("请在浏览器中登录阿里云控制台")
    logger.info(f"登录状态将保存到: {storage_state_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # 访问阿里云容器镜像服务控制台
        console_url = "https://cr.console.aliyun.com/"
        logger.info(f"访问控制台: {console_url}")
        page = context.new_page()
        page.goto(console_url)

        # 等待用户手动登录
        input("\n登录完成后按回车键继续...")

        # 保存登录状态
        state_file = Path(storage_state_path)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        context.storage_state(path=str(state_file))
        browser.close()

        # 设置文件权限为只有所有者可读写
        os.chmod(str(state_file), 0o600)

        logger.info(f"✓ 登录状态已保存到: {storage_state_path}")
        return True


def verify_login_state(storage_state_path: str) -> bool:
    """验证登录状态文件是否有效

    Args:
        storage_state_path: 登录状态文件路径

    Returns:
        登录状态是否有效
    """
    state_file = Path(storage_state_path)

    # 检查文件是否存在
    if not state_file.exists():
        logger.error(f"登录状态文件不存在: {storage_state_path}")
        return False

    # 读取并验证文件内容
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)

        # 检查是否包含 cookies
        if not state.get('cookies'):
            logger.error("登录状态文件无效：未找到 cookies")
            return False

        # 检查 cookies 是否包含必要的信息
        cookies = state['cookies']
        has_valid_cookie = any(
            cookie.get('domain', '').endswith('aliyun.com')
            and cookie.get('expires', -1) > 0
            for cookie in cookies
        )

        if not has_valid_cookie:
            logger.warning("登录状态可能已过期")
            return False

        logger.debug("登录状态验证通过")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"登录状态文件格式错误: {e}")
        return False
    except Exception as e:
        logger.error(f"验证登录状态时出错: {e}")
        return False
