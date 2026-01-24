# 分页查找功能 - 使用说明

## ✅ 新功能概述

`delete_single_tag` 方法现在支持**自动翻页查找** tag!

当当前页面未找到目标 tag 时,会自动点击"下一页"按钮继续查找,最多查找 10 页。

## 🔧 工作原理

### 执行流程

```
1. 访问镜像页面
   ↓
2. 在当前页查找 tag
   ↓
3. 找到了?
   ├─ YES → 执行删除
   └─ NO  → 点击"下一页"按钮
            ↓
4. 进入下一页
   ↓
5. 在新页面查找 tag
   ↓
6. 找到了?
   ├─ YES → 执行删除
   └─ NO  → 继续翻页 (最多10页)
```

### 关键特性

1. **智能翻页**: 自动识别多种"下一页"按钮样式
2. **禁用检测**: 检测按钮是否可点击(避免在最后一页点击)
3. **页码记录**: 日志中显示在第几页找到 tag
4. **最大页数限制**: 默认最多查找 10 页(可配置)

## 📝 代码变更

### 1. delete_single_tag 方法签名变更

**修改前:**
```python
def delete_single_tag(self, tag: str) -> bool:
```

**修改后:**
```python
def delete_single_tag(self, tag: str, max_pages: int = 10) -> bool:
```

### 2. 新增辅助方法

#### _click_next_page()
点击"下一页"按钮的方法

支持的选择器:
- `.next-pagination-item.next-next` - NextUI 分页组件 (阿里云实际使用)
- `.next-next` - 简化版 NextUI 选择器
- `button[aria-label*='下一页']` - 通过 aria-label 属性定位
- `.next-btn.next-pagination-item` - 组合类名
- `button.next-pagination-item` - 通用 NextUI 分页按钮

特性:
- 检查按钮是否存在
- 检查按钮是否可点击(非禁用状态)
- 返回是否成功点击

#### _perform_delete()
执行实际删除操作的方法

提取了原有的删除逻辑,使代码更清晰:
- 点击删除按钮
- 确认删除
- 验证删除成功

## 🚀 使用示例

### 基础使用

```bash
# 删除单个 tag (自动翻页查找)
export $(cat .env.beijing | xargs)
uv run cli.py delete-browser-single update-cert-20251010 --show-browser
```

### 自定义最大页数

如果您知道 tag 可能在更后面的页面,可以增加查找页数:

```python
# 修改 browser_deleter.py
from browser_deleter import AliyunBrowserDeleter

with AliyunBrowserDeleter() as deleter:
    deleter.delete_single_tag('my-tag', max_pages=50)  # 查找 50 页
```

### 查看详细日志

使用 `--verbose` 参数查看翻页过程:

```bash
uv run cli.py delete-browser-single my-tag --verbose --show-browser
```

日志输出示例:
```
INFO: 开始删除 tag: update-cert-20251010
DEBUG: 访问页面: https://cr.console.aliyun.com/.../images
INFO: 当前页未找到 tag: update-cert-20251010,尝试翻页查找...
DEBUG: 成功点击下一页按钮
INFO: 进入第 2 页查找...
INFO: 在第 2 页找到 tag: update-cert-20251010
DEBUG: 点击删除按钮
DEBUG: 确认删除
✓ 成功删除 tag: update-cert-20251010
```

## 🎯 实际应用场景

### 场景 1: Tag 在第 5 页

```bash
# 假设 update-cert-20251010 在第 5 页
uv run cli.py delete-browser-single update-cert-20251010

# 程序会:
# 1. 第 1 页 - 未找到
# 2. 点击下一页 → 第 2 页 - 未找到
# 3. 点击下一页 → 第 3 页 - 未找到
# 4. 点击下一页 → 第 4 页 - 未找到
# 5. 点击下一页 → 第 5 页 - 找到! 执行删除
```

### 场景 2: Tag 不存在

```bash
uv run cli.py delete-browser-single non-existent-tag

# 程序会:
# 1. 查找第 1-10 页
# 2. 每页都未找到
# 3. 最终返回失败
```

## ⚙️ 配置选项

### 修改默认最大页数

在 `cli.py` 中添加参数:

```python
@typer.command()
def delete_browser_single(
    tag: str = Argument(..., help="要删除的 tag 名称"),
    headless: bool = Option(True, "--headless/--show-browser"),
    dry_run: bool = Option(False, "--dry-run"),
    verbose: bool = Option(False, "--verbose"),
    max_pages: int = Option(10, "--max-pages", help="最大查找页数")
):
```

### 使用自定义页数

```bash
# 查找最多 50 页
uv run cli.py delete-browser-single my-tag --max-pages 50

# 查找最多 100 页
uv run cli.py delete-browser-single my-tag --max-pages 100
```

## 🔍 调试技巧

### 1. 使用 --show-browser 查看翻页过程

```bash
uv run cli.py delete-browser-single my-tag --show-browser
```

您可以亲眼看到:
- 浏览器自动翻页
- 在哪一页找到 tag
- 删除按钮的点击过程

### 2. 使用 --verbose 查看详细日志

```bash
uv run cli.py delete-browser-single my-tag --verbose
```

日志会显示:
- 每次翻页操作
- 尝试的每个选择器
- 按钮状态(是否禁用)
- 当前页码

### 3. 录制页面结构学习

使用 `quick_record.sh` 录制阿里云页面:

```bash
./quick_record.sh
```

可以查看:
- 下一页按钮的实际选择器
- 删除按钮的位置
- 确认对话框的样式

## 🐛 常见问题

### Q: 下一页按钮点击失败?

**原因**: 页面结构与预期不符，或使用了不同的 UI 框架

**解决**:
1. 使用 `--show-browser` 查看实际页面
2. 使用录制工具获取正确的选择器 (参考 [PLAYWRIGHT_RECORDING.md](PLAYWRIGHT_RECORDING.md))
3. 检查阿里云是否更新了 UI 组件库 (目前使用 NextUI)
4. 更新 `_click_next_page()` 方法中的选择器列表

**当前支持**: NextUI 分页组件 (`.next-pagination-item.next-next`)

### Q: 翻页速度太快?

**原因**: 默认延迟可能不够

**解决**:
1. 增加 `--delay` 参数(需要修改代码)
2. 或在浏览器设置中启用慢动作模式

### Q: 找到了但删除失败?

**原因**: 删除按钮选择器不正确

**解决**:
1. 使用录制工具录制正确的删除流程
2. 更新 `_perform_delete()` 方法中的选择器
3. 使用 `--verbose` 查看详细错误信息

## 📊 性能考虑

- **翻页延迟**: 每次翻页默认延迟 2 秒
- **最大页数**: 最多 10 页(约 200 个 tags,假设每页 20 个)
- **总时间估算**:
  - 1 页: ~5 秒
  - 5 页: ~20 秒
  - 10 页: ~40 秒

## ✅ 测试建议

### 测试翻页功能

```bash
# 1. 使用一个肯定存在的 tag 测试
uv run cli.py delete-browser-single existing-tag --show-browser

# 2. 使用不存在的 tag 测试翻页逻辑
uv run cli.py delete-browser-single non-existing-tag --show-browser

# 3. 使用 verbose 模式查看详细信息
uv run cli.py delete-browser-single existing-tag --verbose --show-browser
```

## 🎉 总结

分页查找功能现在已集成到 `delete_single_tag` 方法中!

**主要改进:**
- ✅ 自动翻页查找 tag
- ✅ 智能识别下一页按钮
- 检测按钮禁用状态
- ✅ 详细的日志输出
- ✅ 可配置最大页数

**无需手动配置**,开箱即用!
