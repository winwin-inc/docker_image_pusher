"""浏览器删除模块

提供通过浏览器自动化删除阿里云镜像标签的功能。
"""

import logging
import os
import re
import time
from typing import Dict, List

from playwright.sync_api import sync_playwright

from ..core.config import Config
from ..registry.tags import get_image_tags
from .selectors import (
    CONFIRM_BUTTON_SELECTORS,
    DELETE_BUTTON_SELECTORS,
    NEXT_PAGE_SELECTORS,
    get_tag_selectors,
)

logger = logging.getLogger(__name__)


class AliyunBrowserDeleter:
    """阿里云浏览器删除器

    使用浏览器自动化技术删除阿里云容器镜像服务的标签。
    """

    def __init__(
        self,
        storage_state_path: str = "data/aliyun_state.json",
        headless: bool = True,
        timeout: int = 30000,
        delay: float = 2.0,
    ):
        """初始化浏览器删除器

        Args:
            storage_state_path: 登录状态文件路径
            headless: 是否使用无头模式
            timeout: 页面操作超时时间(毫秒)
            delay: 操作之间的延迟时间(秒)
        """
        self.storage_state_path = storage_state_path
        self.headless = headless
        self.timeout = timeout
        self.delay = delay

        # 从配置读取
        self.registry = Config.get_registry()
        self.namespace = Config.get_namespace()

        # 构建控制台 URL
        self.base_url = self._build_console_url()

        # Playwright 实例
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        logger.info(f"初始化浏览器删除器: registry={self.registry}, namespace={self.namespace}")

    def connect(self) -> bool:
        """连接到浏览器并加载登录状态

        Returns:
            是否连接成功
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )

            # 加载保存的登录状态
            if os.path.exists(self.storage_state_path):
                logger.debug(f"加载登录状态: {self.storage_state_path}")
                self.context = self.browser.new_context(
                    storage_state=self.storage_state_path, viewport={"width": 1920, "height": 1080}
                )
            else:
                logger.error(f"未找到登录状态文件: {self.storage_state_path}")
                logger.error("请先运行: uv run python cli.py delete-browser-login")
                return False

            self.page = self.context.new_page()
            self.page.set_default_timeout(self.timeout)

            logger.info("浏览器连接成功")
            return True

        except Exception as e:
            logger.error(f"浏览器连接失败: {e}")
            return False

    def delete_single_tag(self, tag: str, max_pages: int = 10) -> bool:
        """删除单个镜像 tag (支持分页查找)

        Args:
            tag: 要删除的 tag 名称
            max_pages: 最大查找页数

        Returns:
            是否删除成功
        """
        logger.info(f"开始删除 tag: {tag}")

        try:
            # 导航到镜像仓库页面
            logger.debug(f"访问页面: {self.base_url}")
            self.page.goto(self.base_url, wait_until="networkidle")

            # 等待页面加载完成
            self._wait_for_page_ready()

            # 在当前页查找 tag
            tag_locator = self._locate_tag_element(tag)
            if tag_locator:
                logger.debug(f"在第 1 页找到 tag: {tag}")
                return self._perform_delete(tag, tag_locator)

            # 当前页未找到,尝试翻页查找
            logger.info(f"当前页未找到 tag: {tag},尝试翻页查找...")

            for page_num in range(2, max_pages + 1):
                if not self._click_next_page():
                    logger.warning("未找到下一页按钮或已到最后一页")
                    break

                logger.info(f"进入第 {page_num} 页查找...")

                # 等待新页面加载完成
                self._wait_for_page_ready()

                # 在新页面查找 tag
                tag_locator = self._locate_tag_element(tag)
                if tag_locator:
                    logger.info(f"在第 {page_num} 页找到 tag: {tag}")
                    return self._perform_delete(tag, tag_locator)

            logger.error(f"在 {max_pages} 页内未找到 tag: {tag}")
            return False

        except Exception as e:
            logger.error(f"删除 tag {tag} 时出错: {e}")
            return False

    def delete_batch_tags(self, tags: List[str]) -> Dict[str, bool]:
        """批量删除多个标签

        Args:
            tags: 要删除的标签列表

        Returns:
            删除结果字典 {tag: success}
        """
        logger.info(f"开始批量删除 {len(tags)} 个标签")
        results = {}

        # 首先获取所有现有 tags
        all_tags = get_image_tags()
        existing_tags = [tag for tag in tags if tag in all_tags]

        if not existing_tags:
            logger.warning("没有找到任何要删除的标签")
            return {tag: False for tag in tags}

        logger.info(f"找到 {len(existing_tags)} 个已存在的标签")

        # 导航到页面
        self.page.goto(self.base_url, wait_until="networkidle")
        self._wait_for_page_ready()

        for i, tag in enumerate(existing_tags, 1):
            logger.info(f"[{i}/{len(existing_tags)}] 删除 tag: {tag}")

            # 在当前页查找并删除
            tag_locator = self._locate_tag_element(tag)
            if tag_locator:
                success = self._perform_delete(tag, tag_locator)
                results[tag] = success

                # 等待一段时间，避免操作过快
                if success and i < len(existing_tags):
                    time.sleep(self.delay)
            else:
                logger.warning(f"未找到 tag: {tag}")
                results[tag] = False

        # 统计结果
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"批量删除完成: 成功 {success_count}/{len(existing_tags)}")

        return results

    def delete_regex_tags(self, pattern: str, limit: int = 100) -> Dict[str, bool]:
        """按正则表达式批量删除标签

        Args:
            pattern: 正则表达式模式
            limit: 最大删除数量

        Returns:
            删除结果字典
        """
        import re as regex_module

        logger.info(f"开始按正则表达式删除: pattern={pattern}")

        # 编译正则表达式
        try:
            regex = regex_module.compile(pattern)
        except regex_module.error as e:
            logger.error(f"无效的正则表达式: {e}")
            return {}

        # 获取所有标签
        all_tags = get_image_tags()
        if not all_tags:
            logger.warning("未找到任何标签")
            return {}

        # 过滤匹配的标签
        matched_tags = [tag for tag in all_tags if regex.match(tag)]

        if not matched_tags:
            logger.warning(f"没有标签匹配模式: {pattern}")
            return {}

        # 限制数量
        if len(matched_tags) > limit:
            logger.info(f"匹配到 {len(matched_tags)} 个标签，但限制为 {limit} 个")
            matched_tags = matched_tags[:limit]

        logger.info(f"将删除 {len(matched_tags)} 个标签")
        logger.debug(f"标签列表: {matched_tags[:10]}...")

        # 批量删除
        results = self.delete_batch_tags(matched_tags)

        return results

    def close(self):
        """关闭浏览器连接"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            logger.info("浏览器连接已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    # ==================== 私有方法 ====================

    def _build_console_url(self) -> str:
        """构建阿里云控制台 URL

        Returns:
            控制台 URL
        """
        # 从 registry 地址提取区域
        # 例如: registry.cn-hangzhou.aliyuncs.com -> cn-hangzhou
        region_match = re.search(r"registry\.([^.]+)\.aliyuncs\.com", self.registry)
        if region_match:
            region = region_match.group(1)
            return f"https://cr.{region}.aliyuncs.com/rep/{self.namespace}"
        else:
            # 默认使用杭州区域
            return f"https://cr.console.aliyun.com/rep/{self.namespace}"

    def _wait_for_page_ready(self):
        """等待页面加载完成"""
        time.sleep(self.delay)

    def _locate_tag_element(self, tag: str):
        """定位指定 tag 的元素

        Args:
            tag: 标签名称

        Returns:
            元素定位器或 None
        """
        selectors = get_tag_selectors(tag)

        for selector in selectors:
            try:
                locator = self.page.locator(selector).first
                if locator.count() > 0:
                    logger.debug(f"使用选择器找到元素: {selector}")
                    return locator
            except Exception:
                continue

        logger.warning(f"未找到 tag 元素: {tag}")
        return None

    def _perform_delete(self, tag: str, tag_locator) -> bool:
        """执行删除操作

        Args:
            tag: 标签名称
            tag_locator: 标签元素定位器

        Returns:
            是否删除成功
        """
        try:
            # 1. 滚动到元素位置
            tag_locator.scroll_into_view_if_needed()
            time.sleep(0.5)

            # 2. 查找并点击删除按钮
            delete_button = None
            for selector in DELETE_BUTTON_SELECTORS:
                try:
                    # 在 tag 元素的父元素中查找删除按钮
                    row = tag_locator.locator("xpath=../../..")
                    delete_button = row.locator(selector).first
                    if delete_button.count() > 0:
                        logger.debug(f"找到删除按钮: {selector}")
                        break
                except Exception:
                    continue

            if not delete_button or delete_button.count() == 0:
                logger.error("未找到删除按钮")
                return False

            # 点击删除按钮
            delete_button.click()
            logger.debug("已点击删除按钮")
            time.sleep(self.delay)

            # 3. 处理确认对话框
            confirm_button = None
            for selector in CONFIRM_BUTTON_SELECTORS:
                try:
                    confirm_button = self.page.locator(selector).first
                    if confirm_button.count() > 0:
                        logger.debug(f"找到确认按钮: {selector}")
                        break
                except Exception:
                    continue

            if confirm_button and confirm_button.count() > 0:
                confirm_button.click()
                logger.info(f"成功删除 tag: {tag}")
                time.sleep(self.delay)
                return True
            else:
                logger.error("未找到确认按钮")
                return False

        except Exception as e:
            logger.error(f"执行删除时出错: {e}")
            return False

    def _click_next_page(self) -> bool:
        """点击下一页按钮

        Returns:
            是否成功点击
        """
        for selector in NEXT_PAGE_SELECTORS:
            try:
                button = self.page.locator(selector).first
                if button.count() > 0 and button.is_enabled():
                    button.click()
                    logger.debug("已点击下一页")
                    time.sleep(self.delay)
                    return True
            except Exception:
                continue

        return False
