# WinWin Image Mirror

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

使用 GitHub Action 将国外 Docker 镜像转存到阿里云私有仓库，供国内服务器高速拉取。

## 特性

- 支持 DockerHub、gcr.io、k8s.io、ghcr.io 等任意镜像仓库
- 支持最大 40GB 的大型镜像
- 使用阿里云官方线路，速度快
- 支持多架构镜像（通过 `--platform` 参数）
- 自动处理镜像重名和别名

## 快速开始

### 1. 配置阿里云容器镜像服务

登录 [阿里云容器镜像服务](https://cr.console.aliyun.com/)，启用个人实例，创建一个命名空间。

在「访问凭证」中获取以下环境变量：

| 环境变量 | 说明 |
|---------|------|
| `ALIYUN_REGISTRY` | 仓库地址，如 `registry.cn-hangzhou.aliyuncs.com` |
| `ALIYUN_NAME_SPACE` | 命名空间名称 |
| `ALIYUN_REGISTRY_USER` | 用户名 |
| `ALIYUN_REGISTRY_PASSWORD` | 密码 |

![配置示例](doc/命名空间.png)

### 2. Fork 本项目

Fork 本仓库后，进入 **Actions** 页面启用 GitHub Action。

### 3. 配置环境变量

进入 **Settings → Secrets and variables → Actions → New repository secret**，添加上一步获取的四个环境变量：

- `ALIYUN_REGISTRY`
- `ALIYUN_NAME_SPACE`
- `ALIYUN_REGISTRY_USER`
- `ALIYUN_REGISTRY_PASSWORD`

![配置环境变量](doc/配置环境变量.png)

### 4. 添加镜像

编辑 `images.yaml` 文件，添加需要转存的镜像：

```yaml
# 基础格式
- name: alpine

# 指定标签
- name: alpine:3.18

# 指定仓库
- name: library/nginx:latest

# 使用别名
- name: xhofe/alist
  alias: alist

# 指定架构
- name: alpine
  platform: linux/arm64

# 注释行（以 # 开头）
# - name: commented-image
```

提交后自动触发 GitHub Action 构建。

### 5. 拉取镜像

镜像同步完成后，在阿里云容器镜像服务中查看镜像状态（可设为公开以免登录）。

```bash
docker pull registry.cn-hangzhou.aliyuncs.com/shrimp-images/alpine
```

地址格式：`{ALIYUN_REGISTRY}/{ALIYUN_NAME_SPACE}/{镜像名}:{标签}`

## 本地使用

### 环境要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)（推荐的包管理工具）

### 安装与配置

```bash
# 克隆项目
git clone https://github.com/tech-shrimp/docker_image_pusher.git
cd docker_image_pusher

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入阿里云凭证
```

### 命令行使用

```bash
# 列出已同步的镜像
uv run cli list

# 推送镜像（模拟运行）
uv run cli push --dry-run

# 推送镜像
uv run cli push
```

## 高级功能

### 多架构支持

在 `images.yaml` 中使用 `--platform` 参数指定镜像架构：

```yaml
- name: alpine
  platform: linux/arm64
```

指定后的架构会作为前缀添加到镜像名中。

### 镜像重名处理

程序自动检测同名但不同命名空间的镜像，将源命名空间作为前缀：

```yaml
xhofe/alist    # → shrimp-images/xhofe-alist
xiaoyaliu/alist # → shrimp-images/xiaoyaliu-alist
```

### 定时执行

修改 `.github/workflows/docker.yaml`，添加 schedule 触发器：

```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # 每周日 UTC 0:00 执行
```

### 删除镜像 Tag

通过 Docker Registry API 删除不需要的镜像标签：

```bash
# 删除单个标签
uv run cli delete v1.0.0

# 批量删除
uv run cli delete --batch "v1.0.0 v1.0.1"

# 预览模式（不实际删除）
uv run cli delete --dry-run --batch "v1.0.0 v1.0.1"

# 跳过确认
uv run cli delete --force --batch "v1.0.0 v1.0.1"

# 按正则表达式删除
uv run cli delete --regex "^test-.*"

# 限制删除数量
uv run cli delete --regex "^2025.*" --limit 50
```

## 项目结构

```
winwin-image-mirror/
├── cli.py                 # 命令行入口
├── images.yaml            # 镜像配置文件
├── pyproject.toml         # 项目配置
├── src/winwin_image_mirror/
│   ├── main.py           # CLI 主程序
│   ├── commands/         # 命令模块
│   ├── core/             # 核心配置
│   ├── image/            # 镜像处理
│   └── registry/         # 仓库接口
├── scripts/              # 辅助脚本
└── tests/               # 测试文件
```

## 常见问题

**Q: 镜像拉取失败怎么办？**

检查阿里云容器镜像服务的镜像状态，确保命名空间和镜像名称正确。

**Q: 如何提高同步速度？**

- 只保留需要的镜像，删除不需要的 Tag
- 使用 `--platform` 指定特定架构，减少多架构同步开销

**Q: GitHub Action 运行失败？**

查看 Actions 日志排查问题，常见原因包括网络超时、阿里云配额限制等。

## 视频教程

[bilibili](https://www.bilibili.com/video/BV1Zn4y19743/)

## License

Apache License 2.0 - see [LICENSE](LICENSE) 文件

作者：[技术爬爬虾](https://github.com/tech-shrimp/me)
