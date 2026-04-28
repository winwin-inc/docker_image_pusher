"""页面选择器定义

集中管理所有用于浏览器自动化的 CSS 选择器。
"""


# 下一页按钮选择器
NEXT_PAGE_SELECTORS = [
    "button:has-text('下一页')",
    "button:has-text('Next')",
    "[data-testid='next-page-btn']",
]

# 上一页按钮选择器
PREV_PAGE_SELECTORS = [
    "button:has-text('上一页')",
    "button:has-text('Previous')",
    "[data-testid='prev-page-btn']",
]

# Tag 元素选择器模板
def get_tag_selectors(tag: str) -> list:
    """获取定位指定 tag 元素的选择器列表

    Args:
        tag: 标签名称

    Returns:
        选择器列表（按优先级排序）
    """
    return [
        f"[data-tag='{tag}']",  # 最稳定的 data 属性
        f"tr:has-text('{tag}')",  # 表格行定位
        f".tag-item:has-text('{tag}')",  # CSS 类定位
        f".ant-table-row:has-text('{tag}')",  # Ant Design 组件
        f"td:has-text('{tag}')",  # 表格单元格
    ]


# 删除按钮选择器
DELETE_BUTTON_SELECTORS = [
    "button[data-testid='delete-tag-btn']",
    ".delete-btn",
    "button:has-text('删除')",
]

# 确认对话框按钮选择器
CONFIRM_BUTTON_SELECTORS = [
    "button:has-text('确定')",
    "button:has-text('确认')",
    ".ant-modal .ant-btn-primary",
    "[data-testid='confirm-btn']",
]

# 取消按钮选择器
CANCEL_BUTTON_SELECTORS = [
    "button:has-text('取消')",
    "button:has-text('Cancel')",
    ".ant-modal .ant-btn-default",
]

# 页码选择器
PAGE_NUMBER_SELECTOR = ".ant-pagination-item-active"
PAGE_INPUT_SELECTOR = "input.ant-pagination-options"
