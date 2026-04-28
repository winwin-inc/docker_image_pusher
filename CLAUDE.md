# WinWin Image Mirror - 项目说明文档

## 项目概述

WinWin Image Mirror 是一个用于将国外 Docker 镜像转存到阿里云私有仓库的工具,主要解决国内访问国外镜像源速度慢的问题。

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
winwin-image-mirror/
├── src/winwin_image_mirror/
│   ├── main.py                # CLI 主程序 (Typer)
│   ├── commands/              # 命令模块
│   │   ├── list.py            # 列出已推送的镜像
│   │   ├── push.py            # 推送镜像
│   │   └── delete_browser/    # 浏览器删除命令
│   ├── core/
│   │   └── config.py          # 配置管理
│   ├── image/
│   │   ├── parser.py          # 镜像解析
│   │   └── pusher.py          # 镜像推送
│   └── registry/
│       ├── auth.py             # 认证
│       └── tags.py             # 标签管理
├── scripts/                   # 辅助脚本
├── tests/                     # 测试文件
├── images.yaml                # 镜像配置文件
└── pyproject.toml             # Python 项目配置
```

**核心模块说明:**

- **main.py**: CLI 入口，定义 `list`、`push`、`delete` 等命令
- **image/parser.py**: 解析 `images.yaml`，处理镜像名称转换和重名
- **image/pusher.py**: 执行 docker pull → tag → push 流程
- **registry/tags.py**: 调用 Docker Registry API v2 管理镜像标签

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
uv run cli list

# 推送新镜像(dry-run 模式)
uv run cli push --dry-run

# 推送新镜像
uv run cli push

# 删除镜像标签
uv run cli delete v1.0.0
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

### 镜像处理逻辑

1. **镜像名称解析**: 解析 `name:tag` 格式
2. **冲突检测**: 检查是否存在同名不同命名空间的镜像
3. **名称转换**: 将源镜像名转换为阿里云格式
   - 格式: `{registry}/{namespace}/{image}:{tag}`
4. **Docker 操作**: 执行 pull → tag → push 流程

### Registry API 调用

- **认证**: 支持 Basic Auth 和 Bearer Token
- **标签获取**: `GET /v2/<name>/tags/list`
- **标签删除**: `DELETE /v2/<name>/manifests/<reference>`

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

测试文件位于 `tests/` 目录：

- `test_image_parser.py` - 镜像解析测试
- `test_registry_client.py` - Registry API 测试
- `test_config.py` - 配置管理测试
- `test_browser_delete.py` - 浏览器删除测试

运行测试：`uv run pytest`
