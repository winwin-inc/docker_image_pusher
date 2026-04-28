#!/usr/bin/env python3
"""
阿里云容器镜像服务 - 浏览器自动化删除模块

使用 Playwright 自动化浏览器操作,删除阿里云容器镜像服务的 tags。
适用于 Docker Registry API 返回 401 权限不足的情况。
"""

import os
import json
import time
import re
import logging
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Locator

logger = logging.getLogger(__name__)


class AliyunBrowserDeleter:
    """
    阿里云浏览器自动化删除器

    使用 Playwright 自动化浏览器操作,删除阿里云容器镜像服务的 tags

    Attributes:
        storage_state_path: 登录状态保存路径
        headless: 是否使用无头模式
        timeout: 页面操作超时时间(毫秒)
        delay: 操作之间的延迟时间(秒)
        registry: 阿里云 registry 地址
        namespace: 命名空间
        base_url: 阿里云控制台基础 URL
    """

    def __init__(
        self,
        storage_state_path: str = "data/aliyun_state.json",
        headless: bool = True,
        timeout: int = 30000,
        delay: float = 2.0
    ):
        """
        初始化浏览器删除器

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

        # 从环境变量读取配置
        self.registry = os.getenv('ALIYUN_REGISTRY')
        self.namespace = os.getenv('ALIYUN_NAME_SPACE')

        if not self.registry or not self.namespace:
            raise ValueError("缺少环境变量: ALIYUN_REGISTRY, ALIYUN_NAME_SPACE")

        # 构建控制台 URL
        self.base_url = self._build_console_url()

        # Playwright 实例
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        logger.info(f"初始化浏览器删除器: registry={self.registry}, namespace={self.namespace}")

    def connect(self) -> bool:
        """
        连接到浏览器并加载登录状态

        Returns:
            是否连接成功
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            # 加载保存的登录状态
            if os.path.exists(self.storage_state_path):
                logger.debug(f"加载登录状态: {self.storage_state_path}")
                self.context = self.browser.new_context(
                    storage_state=self.storage_state_path,
                    viewport={'width': 1920, 'height': 1080}
                )
            else:
                logger.error(f"未找到登录状态文件: {self.storage_state_path}")
                logger.error("请先运行: cli.py delete-browser-login")
                return False

            self.page = self.context.new_page()
            self.page.set_default_timeout(self.timeout)

            logger.info("浏览器连接成功")
            return True

        except Exception as e:
            logger.error(f"浏览器连接失败: {e}")
            return False

    def delete_single_tag(self, tag: str, max_pages: int = 10) -> bool:
        """
        删除单个镜像 tag (支持分页查找)

        Args:
            tag: 要删除的 tag 名称
            max_pages: 最大查找页数

        Returns:
            是否删除成功
        """
        logger.info(f"开始删除 tag: {tag}")

        try:
            # 1. 导航到镜像仓库页面
            logger.debug(f"访问页面: {self.base_url}")
            self.page.goto(self.base_url, wait_until="networkidle")

            # 2. 等待页面加载完成
            self._wait_for_page_ready()

            # 3. 在当前页查找 tag
            tag_locator = self._locate_tag_element(tag)
            if tag_locator:
                logger.debug(f"在第 1 页找到 tag: {tag}")
                return self._perform_delete(tag, tag_locator)

            # 4. 当前页未找到,尝试翻页查找
            logger.info(f"当前页未找到 tag: {tag},尝试翻页查找...")

            for page_num in range(2, max_pages + 1):
                if not self._click_next_page():
                    logger.warning(f"未找到下一页按钮或已到最后一页")
                    break

                logger.info(f"进入第 {page_num} 页查找...")
                
                # 等待新页面加载完成
                self._wait_for_page_ready()
                
                # 在新页面查找 tag
                tag_locator = self._locate_tag_element(tag)
                if tag_locator:
                    logger.info(f"在第 {page_num} 页找到 tag: {tag}")
                    return self._perform_delete(tag, tag_locator)

                logger.debug(f"第 {page_num} 页也未找到 tag: {tag}")

            logger.warning(f"在 {max_pages} 页中均未找到 tag: {tag}")
            return False

        except Exception as e:
            logger.error(f"删除 tag {tag} 时发生错误: {e}")
            return False

    def _click_next_page(self) -> bool:
        """
        点击"下一页"按钮 (支持 NextUI 分页组件)

        Returns:
            是否成功点击下一页
        """
        try:
            # NextUI 分页组件选择器 (阿里云实际使用)
            # 按优先级排序，最具体的在前
            next_selectors = [
                ".next-pagination-item.next-next",  # NextUI 下一页按钮 (最具体)
                "button[aria-label*='下一页']",  # 通过 aria-label 属性
                ".next-next",  # 简化版
            ]
            
            # 先检查是否有任何可用的下一页按钮
            any_enabled_button = False
            
            for selector in next_selectors:
                try:
                    next_button = self.page.locator(selector).first
                    if next_button.count() > 0 and next_button.is_enabled():
                        any_enabled_button = True
                        break
                except Exception:
                    continue
            
            # 如果没有找到任何可用的下一页按钮，说明已到最后一页
            if not any_enabled_button:
                logger.debug("所有下一页按钮都已禁用，已到最后一页")
                return False

            # 尝试点击可用的按钮
            for selector in next_selectors:
                try:
                    next_button = self.page.locator(selector).first

                    if next_button.count() == 0:
                        logger.debug(f"选择器未找到元素: {selector}")
                        continue

                    # 检查按钮是否可点击(不是禁用状态)
                    if not next_button.is_enabled():
                        logger.debug(f"下一页按钮已禁用: {selector}")
                        continue

                    # 记录当前URL，用于验证翻页是否成功
                    old_url = self.page.url
                    logger.debug(f"翻页前 URL: {old_url}")
                    
                    # 尝试多种点击方式，处理浮层遮挡问题
                    click_success = False
                    
                    # 方法1: 普通点击
                    try:
                        next_button.click()
                        click_success = True
                        logger.debug("使用普通点击成功")
                    except Exception as e:
                        logger.debug(f"普通点击失败: {e}")
                        
                        # 方法2: 强制点击 (绕过浮层)
                        try:
                            next_button.click(force=True)
                            click_success = True
                            logger.debug("使用强制点击成功")
                        except Exception as e2:
                            logger.debug(f"强制点击也失败: {e2}")
                            
                            # 方法3: 使用 JavaScript 点击 (最可靠)
                            try:
                                self.page.evaluate("(element) => element.click()", next_button)
                                click_success = True
                                logger.debug("使用 JavaScript 点击成功")
                            except Exception as e3:
                                logger.debug(f"JavaScript 点击也失败: {e3}")
                                continue
                    
                    if not click_success:
                        continue
                    
                    logger.debug("成功点击下一页按钮")
                    
                    # 等待页面跳转或内容更新
                    time.sleep(self.delay)
                    
                    # 验证翻页是否成功 (URL变化或页面元素变化)
                    new_url = self.page.url
                    if new_url != old_url:
                        logger.debug(f"翻页后 URL: {new_url} (URL已变化)")
                        return True
                    
                    # 如果URL没变，检查页面内容是否更新
                    # 等待表格内容重新加载
                    try:
                        self.page.wait_for_selector(".next-table-row", timeout=3000)
                        logger.debug("检测到页面内容已更新")
                        return True
                    except Exception:
                        logger.debug(f"未检测到页面变化，选择器: {selector}")
                        continue

                except Exception as e:
                    logger.debug(f"尝试选择器 {selector} 失败: {e}")
                    continue

            logger.debug("未找到可用的下一页按钮")
            return False

        except Exception as e:
            logger.error(f"点击下一页时发生错误: {e}")
            return False

    def _perform_delete(self, tag: str, tag_locator) -> bool:
        """
        执行实际的删除操作

        Args:
            tag: tag 名称
            tag_locator: tag 的定位器

        Returns:
            是否删除成功
        """
        try:
            # 点击删除按钮
            # 支持多种删除按钮选择器 (NextUI 风格)
            delete_button_selectors = [
                ".wind-rc-actions-item:has-text('删除')",  # NextUI 阿里云风格
                "span.wind-rc-actions-item span:has-text('删除')",  # 更具体的 NextUI
                "button[data-testid='delete-tag-btn']",  # 标准 data 属性
                ".delete-btn",  # CSS 类
                "button:has-text('删除')",  # 按钮
                "span:has-text('删除')",  # span 元素
                "a:has-text('删除')",  # 链接
            ]
            
            delete_button = None
            for selector in delete_button_selectors:
                try:
                    btn = tag_locator.locator(selector).first
                    if btn.count() > 0:
                        delete_button = btn
                        logger.debug(f"找到删除按钮: {selector}")
                        break
                except Exception:
                    continue
            
            if not delete_button or delete_button.count() == 0:
                logger.error(f"未找到删除按钮: {tag}")
                return False

            delete_button.click()
            logger.debug("点击删除按钮")

            # 确认删除
            time.sleep(self.delay)
            
            # 等待确认对话框出现
            try:
                self.page.wait_for_selector(".next-dialog", timeout=5000)
                logger.debug("确认对话框已出现")
            except Exception:
                logger.warning("未检测到确认对话框")
            
            # 第一步：勾选"确定删除该版本的镜像"复选框
            checkbox_selectors = [
                ".next-checkbox-label:has-text('确定删除该版本的镜像')",  # NextUI 复选框标签
                "label:has-text('确定删除该版本的镜像')",  # 通用 label
                ".next-checkbox-wrapper:has-text('确定删除该版本的镜像')",  # 复选框容器
            ]
            
            checkbox_clicked = False
            for selector in checkbox_selectors:
                try:
                    checkbox = self.page.locator(selector).first
                    if checkbox.count() > 0:
                        checkbox.click()
                        logger.debug(f"已勾选复选框: {selector}")
                        checkbox_clicked = True
                        time.sleep(0.5)  # 等待复选框状态更新
                        break
                except Exception as e:
                    logger.debug(f"尝试勾选复选框失败 ({selector}): {e}")
                    continue
            
            if not checkbox_clicked:
                logger.warning("未找到或未能勾选复选框，尝试直接点击确认按钮")
            
            # 第二步：查找并点击确认按钮
            confirm_button_selectors = [
                # NextUI Dialog 确定按钮 (阿里云实际使用)
                ".next-dialog-footer .next-btn-primary",  # Dialog footer 中的主要按钮
                ".next-dialog .next-btn-primary.is-wind",  # NextUI Dialog + wind 主题
                "button.next-btn-primary:has(.next-btn-helper:has-text('确定'))",  # 通过 helper span
                "button.next-btn-primary:has-text('确定')",  # 直接文本匹配
                ".next-btn-primary.is-wind",  # wind 主题主要按钮
                
                # 备用选择器
                ".next-dialog-footer button:has-text('确定')",  # Dialog footer 按钮
                "button.next-btn:has-text('确定')",  # 通用 NextUI 按钮
                "button:has-text('确定')",  # 通用按钮
                "button:has-text('确认')",  # 备用文本
                ".ant-modal .ant-btn-primary",  # Ant Design Modal (备用)
                ".ant-popconfirm .ant-btn-primary",  # Ant Design Popconfirm (备用)
            ]
            
            confirm_button = None
            for selector in confirm_button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0:
                        # 检查按钮是否从禁用状态变为可用
                        try:
                            # 等待最多 3 秒让按钮变为可用（勾选复选框后应该很快）
                            btn.wait_for(state="enabled", timeout=3000)
                            logger.debug(f"确认按钮已启用: {selector}")
                        except Exception:
                            # 如果等待超时,检查是否本来就是可用的
                            if btn.is_enabled():
                                logger.debug(f"确认按钮已可用: {selector}")
                            else:
                                logger.debug(f"确认按钮仍被禁用: {selector}")
                                continue
                        
                        confirm_button = btn
                        logger.debug(f"找到确认按钮: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"尝试选择器 {selector} 失败: {e}")
                    continue
            
            if confirm_button and confirm_button.count() > 0:
                confirm_button.click()
                logger.debug("确认删除")
            else:
                logger.warning("未找到确认按钮,可能已自动删除")

            # 等待删除完成
            time.sleep(self.delay * 2)

            # 验证删除成功 - 重新访问页面
            logger.debug(f"重新访问页面验证删除: {self.base_url}")
            self.page.goto(self.base_url, wait_until="networkidle")
            time.sleep(self.delay)

            if not self._locate_tag_element(tag):
                logger.info(f"✓ 成功删除 tag: {tag}")
                return True
            else:
                logger.error(f"✗ 删除失败,tag 仍然存在: {tag}")
                return False

        except Exception as e:
            logger.error(f"执行删除操作时发生错误: {e}")
            return False

    def delete_batch_tags(self, tags: List[str]) -> Dict[str, bool]:
        """
        批量删除多个 tags (优化版 - 每页批量查找并删除)

        Args:
            tags: 要删除的 tag 列表

        Returns:
            字典: {tag: 是否删除成功}
        """
        logger.info(f"开始批量删除 {len(tags)} 个 tags")
        
        # 使用集合提高查找效率
        remaining_tags = set(tags)
        results = {tag: False for tag in tags}
        page_num = 1
        
        try:
            # 1. 访问镜像仓库页面
            logger.debug(f"访问页面: {self.base_url}")
            self.page.goto(self.base_url, wait_until="networkidle")
            
            # 2. 等待页面加载完成
            self._wait_for_page_ready()
            
            # 3. 逐页查找并删除
            while remaining_tags and page_num <= 50:  # 最多查找50页
                logger.info(f"扫描第 {page_num} 页...")
                
                # 在当前页查找所有要删除的 tags
                found_on_page = self._find_tags_on_page(remaining_tags)
                
                if found_on_page:
                    logger.info(f"第 {page_num} 页找到 {len(found_on_page)} 个 tags")
                    
                    # 在当前页删除找到的 tags
                    for i, tag in enumerate(found_on_page, 1):
                        print(f"\n  [{len(tags) - len(remaining_tags) + 1}/{len(tags)}] 删除 tag: {tag}", flush=True)
                        
                        # 从页面读取真实页码（删除前记录）
                        current_page_before_delete = self._get_current_page_number()
                        logger.debug(f"删除前在第 {current_page_before_delete} 页")
                        
                        # 定位 tag 元素
                        tag_locator = self._locate_tag_element(tag)
                        if tag_locator:
                            success = self._perform_delete(tag, tag_locator)
                            results[tag] = success
                            
                            if success:
                                logger.info(f"✓ 成功删除 tag: {tag}")
                                remaining_tags.remove(tag)
                                
                                # 删除后页面会刷新回到第一页，需要跳转回之前的页面
                                if i < len(found_on_page):  # 如果还有更多 tags 要删除
                                    logger.debug(f"删除完成，跳转回第 {current_page_before_delete} 页继续删除")
                                    if current_page_before_delete > 1:
                                        self._goto_page(current_page_before_delete)
                            else:
                                logger.warning(f"✗ 删除失败: {tag}")
                            
                            # 删除后等待页面稳定
                            time.sleep(self.delay)
                        else:
                            logger.warning(f"未找到 tag 元素: {tag}")
                            results[tag] = False
                
                # 检查是否所有 tags 都已删除
                if not remaining_tags:
                    logger.info("所有 tags 已删除完成")
                    break
                
                # 翻到下一页
                if not self._click_next_page():
                    logger.info("已到最后一页或无法翻页")
                    break
                
                page_num += 1
                self._wait_for_page_ready()
            
            # 输出统计
            success_count = sum(1 for v in results.values() if v)
            failed_count = len(results) - success_count
            not_found_count = len(remaining_tags)
            
            logger.info(f"\n批量删除完成:")
            logger.info(f"  总数: {len(tags)}")
            logger.info(f"  成功: {success_count}")
            logger.info(f"  失败: {failed_count}")
            logger.info(f"  未找到: {not_found_count}")
            
            if remaining_tags:
                logger.warning(f"以下 tags 未找到: {', '.join(remaining_tags)}")
            
            return results
            
        except Exception as e:
            logger.error(f"批量删除过程中发生错误: {e}")
            return results

    def delete_regex_tags(self, pattern: str, limit: int = 100) -> Dict[str, bool]:
        """
        按正则表达式批量删除 tags

        Args:
            pattern: 正则表达式模式
            limit: 最大删除数量

        Returns:
            字典: {tag: 是否删除成功}
        """
        # 导入现有的 API 函数获取所有 tags
        from cli import get_image_tags

        logger.info(f"按正则表达式删除: pattern={pattern}")

        # 获取所有 tags
        all_tags = get_image_tags()
        if not all_tags:
            logger.error("未获取到任何 tags")
            return {}

        # 编译正则表达式
        try:
            regex = re.compile(pattern)
        except re.error as e:
            logger.error(f"无效的正则表达式: {e}")
            return {}

        # 过滤匹配的 tags
        matched_tags = [tag for tag in all_tags if regex.match(tag)]

        if not matched_tags:
            logger.warning(f"没有 tags 匹配模式: {pattern}")
            return {}

        # 限制数量
        if len(matched_tags) > limit:
            logger.warning(f"匹配到 {len(matched_tags)} 个 tags,限制为 {limit} 个")
            matched_tags = matched_tags[:limit]

        logger.info(f"匹配到 {len(matched_tags)} 个 tags")
        for i, tag in enumerate(matched_tags[:10], 1):
            logger.info(f"  {i}. {tag}")
        if len(matched_tags) > 10:
            logger.info(f"  ... 还有 {len(matched_tags) - 10} 个")

        # 批量删除
        return self.delete_batch_tags(matched_tags)

    def close(self):
        """关闭浏览器连接"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        logger.info("浏览器连接已关闭")

    def _build_console_url(self) -> str:
        """构建阿里云控制台 URL"""
        # 从 registry 地址提取区域
        # 例如: registry.cn-beijing.aliyuncs.com -> cn-beijing
        region = self.registry.replace("registry.", "").replace(".aliyuncs.com", "")
        return f"https://cr.console.aliyun.com/repository/{region}/{self.namespace}/images"

    def _wait_for_page_ready(self):
        """等待页面加载完成"""
        # 等待关键元素出现 (支持 NextUI 表格)
        try:
            self.page.wait_for_selector(
                ".next-table, table, .tag-list, .ant-table, [data-testid='tag-list']",
                timeout=self.timeout
            )
            time.sleep(self.delay)
        except Exception as e:
            logger.warning(f"等待页面加载超时: {e}")

    def _locate_tag_element(self, tag: str):
        """
        在页面中定位指定的 tag 元素 (支持 NextUI 表格)

        Args:
            tag: tag 名称

        Returns:
            Playwright Locator 对象或 None
        """
        # NextUI 表格选择器 (阿里云实际使用)
        selectors = [
            # NextUI 表格行 (最准确)
            f".next-table-row:has(.wordBreak:has-text('{tag}'))",  # 通过 wordBreak 类定位
            f"tr.next-table-row:has-text('{tag}')",  # NextUI 表格行 + 文本
            f".next-table-cell:has-text('{tag}')",  # NextUI 表格单元格
            
            # 备用选择器 (兼容其他可能的 UI)
            f"[data-tag='{tag}']",  # data 属性
            f"tr[data-id*='{tag}']",  # 表格行 data-id
            f".image-tag-list tr:has-text('{tag}')",  # 阿里云 tag 列表
            f".ant-table-tbody tr:has-text('{tag}')",  # Ant Design 表格体 (备用)
            f".repo-image-tag:has-text('{tag}')",  # 镜像 tag 元素

            # 通用选择器 (最后备选)
            f"tr:has-text('{tag}')",  # 表格行
            f".tag-item:has-text('{tag}')",  # tag 卡片
            f".ant-table-row:has-text('{tag}')",  # Ant Design 表格行
            f"td:has-text('{tag}')",  # 表格单元格
        ]

        for selector in selectors:
            try:
                locator = self.page.locator(selector).first
                if locator.count() > 0:
                    logger.debug(f"找到 tag 元素: {selector}")
                    return locator
            except Exception:
                continue

        logger.warning(f"未找到 tag 元素: {tag}")
        return None

    def _find_tags_on_page(self, tags: set) -> List[str]:
        """
        在当前页查找多个 tags (批量查找)

        Args:
            tags: 要查找的 tag 集合

        Returns:
            在当前页找到的 tag 列表
        """
        found_tags = []
        
        for tag in tags:
            # 使用简单快速的选择器查找
            try:
                # 优先使用最准确的选择器
                selector = f".next-table-row:has(.wordBreak:has-text('{tag}'))"
                locator = self.page.locator(selector).first
                
                if locator.count() > 0:
                    found_tags.append(tag)
                    logger.debug(f"在当前页找到 tag: {tag}")
            except Exception:
                continue
        
        return found_tags

    def _get_current_page_number(self) -> int:
        """
        获取当前页码（从页面真实读取）

        Returns:
            当前页码，如果无法获取则返回 1
        """
        try:
            # 方法1: 从 URL 中提取页码
            current_url = self.page.url
            if 'pageIndex' in current_url:
                import re
                match = re.search(r'pageIndex=(\d+)', current_url)
                if match:
                    page_num = int(match.group(1))
                    logger.debug(f"从 URL 获取当前页码: {page_num}")
                    return page_num
            
            # 方法2: 查找所有分页按钮，找出激活状态的
            # NextUI 分页中，激活的按钮通常有特定样式
            try:
                # 获取所有数字按钮
                all_page_buttons = self.page.locator(".next-pagination-number").all()
                
                for button in all_page_buttons:
                    try:
                        # 检查是否有激活状态的类
                        class_attr = button.get_attribute("class") or ""
                        if "next-active" in class_attr or "next-btn-primary" in class_attr:
                            # 这是激活的按钮
                            page_text = button.inner_text()
                            if page_text and page_text.strip().isdigit():
                                page_num = int(page_text.strip())
                                logger.debug(f"从激活按钮获取当前页码: {page_num}")
                                return page_num
                    except Exception:
                        continue
            except Exception as e:
                logger.debug(f"查找激活按钮失败: {e}")
            
            # 方法3: 使用 JavaScript 直接读取
            try:
                page_num = self.page.evaluate("""() => {
                    // 查找所有分页数字按钮
                    const buttons = document.querySelectorAll('.next-pagination-number, .next-pagination-item');
                    for (let btn of buttons) {
                        const text = btn.textContent?.trim();
                        if (text && /^\d+$/.test(text)) {
                            // 检查是否激活
                            const isActive = btn.classList.contains('next-active') || 
                                          btn.classList.contains('next-btn-primary') ||
                                          btn.querySelector('.next-btn-primary');
                            if (isActive) {
                                return parseInt(text);
                            }
                        }
                    }
                    return 1;
                }""")
                if page_num and page_num > 1:
                    logger.debug(f"通过 JavaScript 获取当前页码: {page_num}")
                    return page_num
            except Exception as e:
                logger.debug(f"JavaScript 获取页码失败: {e}")
            
            logger.debug("无法获取当前页码，默认为 1")
            return 1
        except Exception as e:
            logger.warning(f"获取当前页码失败: {e}")
            return 1

    def _goto_page(self, page_num: int) -> bool:
        """
        跳转到指定页码

        Args:
            page_num: 目标页码

        Returns:
            是否成功跳转
        """
        try:
            logger.debug(f"尝试跳转到第 {page_num} 页")
            
            # NextUI 分页组件 - 点击指定页码
            page_button_selectors = [
                f".next-pagination-number:has-text('{page_num}')",  # NextUI 数字页码
                f".next-pagination-item:has(.next-btn-helper:has-text('{page_num}'))",  # 通过 helper 文本
                f"button:has-text('{page_num}')",  # 通用按钮文本
            ]
            
            for selector in page_button_selectors:
                try:
                    page_button = self.page.locator(selector).first
                    if page_button.count() > 0:
                        page_button.click()
                        logger.debug(f"成功点击第 {page_num} 页按钮")
                        time.sleep(self.delay)
                        self._wait_for_page_ready()
                        return True
                except Exception as e:
                    logger.debug(f"尝试点击第 {page_num} 页失败 ({selector}): {e}")
                    continue
            
            logger.warning(f"未找到第 {page_num} 页按钮")
            return False
        except Exception as e:
            logger.error(f"跳转到第 {page_num} 页时发生错误: {e}")
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


def save_login_state(
    storage_state_path: str = "data/aliyun_state.json"
) -> bool:
    """
    保存阿里云登录状态到文件

    Args:
        storage_state_path: 保存路径

    Returns:
        是否保存成功
    """
    logger.info("开始保存登录状态...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            # 访问阿里云控制台
            logger.info("打开阿里云控制台...")
            page.goto("https://cr.console.aliyun.com/", wait_until="networkidle")

            # 手动登录
            logger.info("=" * 60)
            logger.info("请在浏览器中手动登录阿里云控制台")
            logger.info("")
            logger.info("登录步骤:")
            logger.info("1. 输入阿里云账号和密码")
            logger.info("2. 完成验证码验证(如有)")
            logger.info("3. 确认已成功登录到控制台")
            logger.info("")
            logger.info("登录成功后,请返回终端按回车键继续...")
            logger.info("=" * 60)

            try:
                input()
            except EOFError:
                logger.error("无法读取输入,请手动运行此命令")
                browser.close()
                return False

            # 验证登录状态 - 等待并检查是否有登录标志
            logger.info("验证登录状态...")
            time.sleep(3)

            # 检查当前URL是否还在登录页面
            current_url = page.url
            logger.debug(f"当前页面URL: {current_url}")

            # 检查cookies
            cookies = context.cookies()
            logger.debug(f"获取到 {len(cookies)} 个 cookies")

            if not cookies:
                logger.error("未检测到登录cookies,可能登录未成功")
                confirm = input("是否仍要保存登录状态? (y/n): ")
                if confirm.lower() != 'y':
                    browser.close()
                    return False

            # 保存状态
            logger.info(f"保存登录状态到: {storage_state_path}")
            context.storage_state(path=storage_state_path)

            browser.close()

            logger.info("✓ 登录状态保存成功")
            logger.info(f"保存位置: {os.path.abspath(storage_state_path)}")
            return True

    except Exception as e:
        logger.error(f"保存登录状态失败: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def verify_login_state(storage_state_path: str = "data/aliyun_state.json") -> bool:
    """
    验证登录状态文件是否有效

    Args:
        storage_state_path: 登录状态文件路径

    Returns:
        是否有效
    """
    if not os.path.exists(storage_state_path):
        logger.debug(f"登录状态文件不存在: {storage_state_path}")
        return False

    try:
        with open(storage_state_path, 'r') as f:
            state = json.load(f)

        # 检查是否有 cookies
        cookies = state.get('cookies', [])
        if not cookies:
            logger.warning("登录状态文件中没有 cookies")
            return False

        # 检查 cookies 是否过期
        import time
        current_time = int(time.time())
        valid_cookies = False

        for cookie in cookies:
            expires = cookie.get('expires', -1)
            # expires == -1 表示会话 cookie,不会过期
            if expires == -1 or expires > current_time:
                valid_cookies = True
                break

        if not valid_cookies:
            logger.warning("登录状态文件中的 cookies 已过期")
            return False

        logger.info("登录状态文件有效")
        return True

    except Exception as e:
        logger.error(f"验证登录状态失败: {e}")
        return False
