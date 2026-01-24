# Docker Image Pusher - 项目结构

## 📁 目录结构

```
docker_image_pusher/
├── cli.py                    # 主命令行工具入口
├── util.py                   # 日志和工具函数
├── browser_deleter.py        # 浏览器自动化删除模块
├── images.yaml               # 镜像配置文件
├── pyproject.toml            # Python 项目配置
├── uv.lock                   # 依赖锁定文件
├── README.md                 # 项目说明文档
├── CLAUDE.md                 # Claude 项目说明
├── LICENSE                   # 许可证
│
├── docs/                     # 📚 详细文档目录
│   ├── README.md             # 文档索引
│   ├── 浏览器删除方案.md     # 浏览器删除设计文档
│   ├── PAGINATION_GUIDE.md   # 分页功能使用指南
│   └── PLAYWRIGHT_RECORDING.md # Playwright 录制指南
│
├── scripts/                  # 🛠️ 脚本工具目录
│   ├── quick_record.sh       # 快速录制 Playwright 操作
│   ├── selector_helper.py    # 选择器辅助工具
│   ├── record_delete.py      # 删除操作录制指南
│   ├── recorded_delete.py    # 录制的删除操作示例
│   ├── delete-with-debug.sh  # 调试脚本
│   └── delete_via_browser.py # 浏览器删除实现
│
├── tests/                    # 🧪 测试目录
│   ├── test.py               # 基础功能测试
│   └── test_browser_delete.py # 浏览器删除功能测试
│
├── data/                     # 📊 数据文件目录
│   ├── images.txt            # 镜像列表文件
│   └── images-beijing.txt    # 北京区域镜像列表
│
├── doc/                      # 📖 文档图片目录
│   ├── 定时执行.png
│   ├── 多架构.png
│   ├── 镜像重名.png
│   ├── 开始使用.png
│   ├── 命名空间.png
│   ├── 配置环境变量.png
│   ├── 用户名密码.png
│   └── images.png
│
└── logs/                    # 📝 日志目录
    └── app-*.log            # 应用日志文件
```

## 📝 核心文件说明

### 主要程序文件

- **cli.py** - 命令行工具主入口，包含所有 CLI 命令
- **util.py** - 日志配置和通用工具函数
- **browser_deleter.py** - Playwright 浏览器自动化删除阿里云镜像 tag

### 配置文件

- **images.yaml** - 定义需要转存的 Docker 镜像列表
- **pyproject.toml** - Python 项目配置和依赖定义
- **uv.lock** - 依赖版本锁定文件
- **.gitignore** - Git 忽略文件配置

### 文档文件

- **README.md** - 项目说明文档
- **CLAUDE.md** - 项目结构和开发指南
- **docs/** - 详细的技术文档

### 环境文件

- **.env** - 环境变量配置（不提交到 Git）
- **aliyun_state.json** - 阿里云登录状态（不提交到 Git）

## 🔧 常用命令

```bash
# 列出镜像
uv run cli.py list

# 推送镜像
uv run cli.py push

# 保存登录状态
uv run cli.py delete-browser-login

# 删除单个 tag
uv run cli.py delete-browser-single v1.0.0

# 批量删除 tags
uv run cli.py delete-browser-batch "v1.0.0 v1.0.1 v1.0.2"

# 正则表达式删除
uv run cli.py delete-browser-regex "^test-.*"
```

## 📖 更多文档

详细文档请查看 [docs/](docs/) 目录。
