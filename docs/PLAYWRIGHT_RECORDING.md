# Playwright 代码录制指南

本文档介绍如何使用 Playwright 录制浏览器操作并生成 Python 代码。

## 🎯 快速开始

### 方法 1: Playwright Codegen (推荐)

**命令格式:**
```bash
uv run playwright codegen <URL> -o <output_file.py>
```

**示例:**
```bash
# 加载环境变量
export $(cat .env.beijing | xargs)

# 录制删除操作
uv run playwright codegen https://cr.console.aliyun.com/repository/cn-beijing/winwin/tool/images -o delete_recorded.py
```

**录制步骤:**
1. 浏览器自动打开
2. 执行您想录制的操作(登录、查找tag、点击删除等)
3. 关闭浏览器窗口或按 Ctrl+C
4. 代码自动保存到 `delete_recorded.py`

### 方法 2: 使用已保存的登录状态录制

```bash
# 先保存登录状态
uv run cli.py delete-browser-login

# 使用 Playwright Inspector 录制
uv run playwright codegen \
  https://cr.console.aliyun.com/repository/cn-beijing/winwin/tool/images \
  --load-storage=aliyun_state.json \
  -o delete_recorded.py
```

### 方法 3: 交互式录制 (最灵活)

```bash
uv run playwright codegen \
  https://cr.console.aliyun.com/repository/cn-beijing/winwin/tool/images \
  --target=python \
  -o delete_recorded.py
```

**参数说明:**
- `--target=python`: 生成 Python 代码
- `--load-storage=aliyun_state.json`: 使用保存的登录状态
- `-o`: 输出文件

## 🔧 实用技巧

### 1. 获取元素选择器

**方法 A: 使用浏览器开发者工具**
```javascript
// 在浏览器控制台运行
// 获取元素的所有属性
const element = document.querySelector('.your-selector');
console.log(element);
console.log(element.className);
console.log(element.id);
console.log(element.dataset);
```

**方法 B: 使用 Playwright Inspector**
```bash
# 启动 Inspector
uv run playwright inspector

# 然后在浏览器中:
# 1. 访问目标页面
# 2. 点击 "Record" 按钮
# 3. 点击 "Pick Locator" (十字准星图标)
# 4. 点击页面上的元素
# 5. 查看生成的选择器
```

**方法 C: 使用辅助脚本**
```bash
# 运行选择器助手
PYTHONPATH=. python selector_helper.py
```

### 2. 测试选择器是否正确

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://cr.console.aliyun.com/repository/cn-beijing/winwin/tool/images")

    # 测试选择器
    locator = page.locator("your-selector-here")

    # 计数
    count = locator.count()
    print(f"找到 {count} 个元素")

    # 获取第一个元素
    if count > 0:
        first = locator.first
        print(f"文本: {first.text_content()}")
        print(f"HTML: {first.inner_html()}")
```

### 3. 常用选择器模式

```python
# 按文本查找
"tr:has-text('update-cert-20251010')"

# 按属性查找
"[data-tag='update-cert-20251010']"
"[data-id*='update-cert']"

# 按 class 查找
".delete-btn"
".ant-btn-primary"

# 组合查找
"button.delete-btn:has-text('删除')"

# 多层级查找
".ant-table tr:has-text('update-cert-20251010') button.delete-btn"
```

## 📝 录制后的代码示例

生成的代码类似这样:

```python
from playwright.sync_api import Playwright, sync_playwright

def run(tag_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        page.goto("https://cr.console.aliyun.com/repository/cn-beijing/winwin/tool/images")

        # 查找 tag
        page.click("tr:has-text('" + tag_name + "')")

        # 点击删除
        page.click("button:has-text('删除')")

        # 确认删除
        page.click("button:has-text('确定')")

        # 等待完成
        page.wait_for_timeout(2000)

        browser.close()

if __name__ == "__main__":
    run("update-cert-20251010")
```

## 🎬 最佳实践

### 1. 录制前的准备

- ✅ 清除浏览器缓存
- ✅ 使用慢动作模式 (`slow_mo=500`)
- ✅ 准备测试数据

### 2. 录制时注意

- ✅ 操作要清晰明确
- ✅ 避免不必要的操作
- ✅ 每次只录制一个功能
- ✅ 使用有意义的数据

### 3. 录制后优化

- ✅ 添加等待和断言
- ✅ 提取可重用函数
- ✅ 添加错误处理
- ✅ 使用描述性变量名

### 4. 调试录制代码

```bash
# 以慢动作模式运行
SLOW_MO=1000 python recorded_script.py

# 显示浏览器运行
HEADLESS=false python recorded_script.py
```

## 🚀 实际应用

### 应用 1: 调试删除功能

```bash
# 1. 录制一次成功的删除操作
uv run playwright codegen \
  https://cr.console.aliyun.com/repository/cn-beijing/winwin/tool/images \
  --load-storage=aliyun_state.json \
  -o working_delete.py

# 2. 查看生成的代码,找到正确的选择器
# 3. 将选择器更新到 src/winwin_image_mirror/browser/deleter.py
```

### 应用 2: 创建测试脚本

```python
def test_delete_tag():
    """测试删除 tag 功能"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state='aliyun_state.json')
        page = context.new_page()

        page.goto("https://cr.console.aliyun.com/.../images")

        # 查找测试 tag
        tag_locator = page.locator("tr:has-text('test-tag')")
        assert tag_locator.count() > 0, "测试 tag 不存在"

        # 删除操作...

        browser.close()
```

## 📚 参考资源

- **Playwright 官方文档**: https://playwright.dev/python/docs/codegen
- **选择器指南**: https://playwright.dev/python/docs/selectors
- **录制最佳实践**: https://playwright.dev/python/docs/best-practices

## 🔍 故障排除

### 问题 1: 录制器无法启动

```bash
# 确保 Playwright 已正确安装
uv run playwright install chromium

# 检查浏览器是否可用
uv run playwright show-browsers
```

### 问题 2: 无法录制登录后的操作

```bash
# 方法 1: 手动登录后录制
uv run cli.py delete-browser-login
uv run playwright codegen <URL> --load-storage=aliyun_state.json

# 方法 2: 使用全窗口录制
uv run playwright codegen <URL> --save-storage=./auth.json
# 然后手动登录,录制会保存认证信息
```

### 问题 3: 生成的代码需要修改

常见修改:
- 添加等待: `page.wait_for_selector()`
- 添加断言: `assert element.is_visible()`
- 提取变量: `tag_name = element.text_content()`
- 添加循环: `for tag in tags:`

## ✅ 总结

使用 Playwright 录制功能的步骤:

1. **准备**: 保存登录状态 (`cli.py delete-browser-login`)
2. **录制**: 使用 `codegen` 录制操作
3. **查看**: 检查生成的代码和选择器
4. **优化**: 添加等待、错误处理
5. **集成**: 将选择器更新到 `src/winwin_image_mirror/browser/deleter.py`
6. **测试**: 运行并验证功能

录制是快速定位问题和学习页面结构的强大工具!
