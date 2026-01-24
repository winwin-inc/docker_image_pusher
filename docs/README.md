# Docker Image Pusher - 文档目录

本文档目录包含项目的详细文档和使用指南。

## 📚 文档列表

### 核心文档

1. **[浏览器删除方案.md](浏览器删除方案.md)**
   - 浏览器自动化删除功能的设计文档
   - 技术实现细节
   - 使用场景说明

2. **[PAGINATION_GUIDE.md](PAGINATION_GUIDE.md)**
   - 分页查找功能使用指南
   - 自动翻页功能说明
   - 常见问题解答

3. **[PLAYWRIGHT_RECORDING.md](PLAYWRIGHT_RECORDING.md)**
   - Playwright 代码录制完整指南
   - 选择器获取技巧
   - 调试和故障排除

## 📖 相关文档

- **[../README.md](../README.md)** - 项目主要说明文档
- **[../CLAUDE.md](../CLAUDE.md)** - 项目说明文档（Claude 使用）

## 🛠️ 脚本工具

位于 `../scripts/` 目录：

- **quick_record.sh** - 快速录制脚本
- **selector_helper.py** - 选择器辅助工具
- **record_delete.py** - 删除操作录制指南
- **delete-with-debug.sh** - 调试删除脚本
- **delete_via_browser.py** - 浏览器删除实现

## 🔧 快速链接

- [GitHub Actions 工作流](../.github/workflows/docker.yaml)
- [镜像配置文件](../images.yaml)
- [测试文件](../tests/)
