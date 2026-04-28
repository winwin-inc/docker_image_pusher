# Docker Image Pusher - 项目说明文档

## 项目概述

Docker Image Pusher 是一个用于将国外 Docker 镜像转存到阿里云私有仓库的工具,主要解决国内访问国外镜像源速度慢的问题。

**主要特性:**
- 支持多种镜像源: DockerHub、gcr.io、k8s.io、ghcr.io 等
- 支持最大 40GB 的大型镜像
- 使用阿里云官方线路,速度快
- 支持多架构镜像(通过 `--platform` 参数)
- 自动处理镜像重名和别名
- 集成 GitHub Actions 自动化构建

**技术栈:**
- Python 3.11+
- Typer: 命令行工具框架
- httpx: HTTP 客户端
- PyYAML: 配置文件解析
- PrettyTable: 表格输出
- uv: 依赖管理工具

**作者:** [技术爬爬虾](https://github.com/tech-shrimp/me)

## 项目结构

```
docker_image_pusher/
├── cli.py                      # 主命令行工具
├── util.py                     # 日志和工具函数
├── images.yaml                 # 镜像配置文件(143个镜像)
├── pyproject.toml              # Python 项目配置
├── README.md                   # 使用文档
├── CLAUDE.md                   # 本文档
├── .github/
│   └── workflows/
│       └── docker.yaml         # GitHub Actions 工作流
├── doc/                        # 配置步骤文档图片
├── tests/                      # 测试文件
│   └── test.py
└── logs/                       # 日志输出目录
```

**核心文件说明:**

- **cli.py**: 包含主要的命令行逻辑
  - `list`: 列出已推送的镜像
  - `push`: 推送新镜像到阿里云
  - `get_image_tags()`: 获取镜像标签列表
  - `delete_image()`: 删除指定镜像

- **util.py**: 日志配置工具
  - 支持文件和控制台双输出
  - 支持大小和时间轮转
  - 支持 JSON 格式日志

- **images.yaml**: 镜像配置文件,定义需要转存的镜像列表

- **.github/workflows/docker.yaml**: GitHub Actions 自动化工作流,实现定时构建

## 核心功能

### 1. Docker 镜像转存机制

项目通过以下流程转存镜像:
1. 从源仓库拉取镜像
2. 重新打标签为目标仓库格式
3. 推送到阿里云私有仓库

### 2. 支持的镜像源

- DockerHub (默认)
- Google Container Registry (gcr.io)
- Kubernetes Registry (k8s.gcr.io)
- GitHub Container Registry (ghcr.io)
- 其他任意 Docker 镜像仓库

### 3. 多架构支持

通过在 [images.yaml](images.yaml) 中指定 `--platform` 参数支持多架构:
```yaml
- name: alpine
  platform: linux/amd64
- name: alpine
  platform: linux/arm64
```

### 4. 别名和重名处理

- **别名**: 使用 `alias` 字段为镜像指定别名
- **重名处理**: 自动检测命名空间冲突,将源命名空间作为前缀添加到镜像名

例如:
```yaml
# 自动处理重名
- name: xhofe/alist        # → shrimp-images/xhofe-alist
- name: xiaoyaliu/alist    # → shrimp-images/xiaoyaliu-alist
```

## 开发环境

### 环境要求

- Python 3.11 或更高版本
- uv (推荐的包管理工具)
- Docker (用于测试镜像推送)

### 依赖安装

```bash
# 使用 uv 安装依赖
uv sync
```

### 环境变量配置

创建 `.env` 文件或设置以下环境变量:

```bash
ALIYUN_REGISTRY=registry.cn-hangzhou.aliyuncs.com
ALIYUN_NAME_SPACE=your-namespace
ALIYUN_REGISTRY_USER=your-username
ALIYUN_REGISTRY_PASSWORD=your-password
```

**获取方式:**
1. 登录 [阿里云容器镜像服务](https://cr.console.aliyun.com/)
2. 创建命名空间 (ALIYUN_NAME_SPACE)
3. 访问凭证 → 获取环境变量
   - 用户名 (ALIYUN_REGISTRY_USER)
   - 密码 (ALIYUN_REGISTRY_PASSWORD)
   - 仓库地址 (ALIYUN_REGISTRY)

## 使用方法

### 本地开发

```bash
# 列出已推送的镜像
uv run cli.py list

# 推送新镜像(dry-run 模式)
uv run cli.py push --dry-run

# 推送新镜像
uv run cli.py push
```

### 镜像配置格式

在 [images.yaml](images.yaml) 中配置需要转存的镜像:

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

# 注释行(以 # 开头)
# - name: commented-image
```

### GitHub Actions 集成

1. Fork 本项目
2. 在 GitHub Settings → Secrets and variables → Actions 中配置环境变量
3. 修改 [images.yaml](images.yaml) 添加需要转存的镜像
4. 提交更改,自动触发构建

### 定时执行

修改 [.github/workflows/docker.yaml](.github/workflows/docker.yaml):

```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # 每周日 UTC 0:00 执行
```

## 关键代码说明

### cli.py 主要函数

**get_image_tags()**: 获取阿里云仓库中的镜像标签列表
- 处理 Docker Registry API v2 认证
- 支持 Basic Auth 和 Bearer Token
- 位置: [cli.py:19](cli.py#L19)

**delete_image()**: 删除指定镜像的特定标签
- 使用 Docker Registry HTTP API v2
- 需要认证 token
- 位置: [cli.py](cli.py)

**push 命令**: 推送镜像的主逻辑
- 解析 [images.yaml](images.yaml)
- 处理镜像名称冲突
- 执行 docker pull, tag, push 操作

### util.py 工具函数

**setup_logging()**: 配置日志系统
- 支持文件和控制台双输出
- 支持轮转(按大小或时间)
- 可选 JSON 格式输出
- 位置: [util.py](util.py)

### 镜像处理逻辑

1. **镜像名称解析**: 解析 `name:tag` 格式
2. **冲突检测**: 检查是否存在同名不同命名空间的镜像
3. **名称转换**: 将源镜像名转换为阿里云格式
   - 格式: `{registry}/{namespace}/{image}:{tag}`
4. **Docker 操作**: 执行 pull → tag → push 流程

## 注意事项

1. **阿里云限制**: 注意阿里云容器的配额限制(命名空间、仓库数量等)
2. **镜像大小**: 大型镜像(>10GB)可能需要较长时间
3. **认证信息**: 不要将 `.env` 文件提交到版本控制
4. **GitHub Secrets**: 确保敏感信息存储在 GitHub Secrets 中
5. **磁盘空间**: GitHub Actions 运行器需要注意磁盘空间,工作流中包含清理步骤
6. **镜像架构**: 使用 `--platform` 时需确保本地或 CI 环境支持该架构
7. **网络问题**: 拉取国外镜像时可能失败,建议使用 GitHub Actions 自动重试

## 相关资源

- 视频教程: https://www.bilibili.com/video/BV1Zn4y19743/
- 阿里云容器镜像服务: https://cr.console.aliyun.com/
- Docker Registry API: https://docs.docker.com/registry/spec/api/

## 测试

测试文件位于 [tests/test.py](tests/test.py):
- 镜像标签获取测试
- 镜像删除功能测试
- 认证 token 获取测试
