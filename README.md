# Docker Images Pusher

使用Github Action将国外的Docker镜像转存到阿里云私有仓库，供国内服务器使用，免费易用<br>
- 支持DockerHub, gcr.io, k8s.io, ghcr.io等任意仓库<br>
- 支持最大40GB的大型镜像<br>
- 使用阿里云的官方线路，速度快<br>

视频教程：https://www.bilibili.com/video/BV1Zn4y19743/

作者：**[技术爬爬虾](https://github.com/tech-shrimp/me)**<br>
B站，抖音，Youtube全网同名，转载请注明作者<br>

## 使用方式


### 配置阿里云
登录阿里云容器镜像服务<br>
https://cr.console.aliyun.com/<br>
启用个人实例，创建一个命名空间（**ALIYUN_NAME_SPACE**）
![](/doc/命名空间.png)

访问凭证–>获取环境变量<br>
用户名（**ALIYUN_REGISTRY_USER**)<br>
密码（**ALIYUN_REGISTRY_PASSWORD**)<br>
仓库地址（**ALIYUN_REGISTRY**）<br>

![](/doc/用户名密码.png)


### Fork本项目
Fork本项目<br>
#### 启动Action
进入您自己的项目，点击Action，启用Github Action功能<br>
#### 配置环境变量
进入Settings->Secret and variables->Actions->New Repository secret
![](doc/配置环境变量.png)
将上一步的**四个值**<br>
ALIYUN_NAME_SPACE,ALIYUN_REGISTRY_USER，ALIYUN_REGISTRY_PASSWORD，ALIYUN_REGISTRY<br>
配置成环境变量

### 添加镜像
打开images.txt文件，先把文件里的内容备份到 all-images.txt 文件中，然后添加你想要的镜像（可以加快构建过程）。<br>
可以加tag，也可以不用(默认latest)<br>
可添加 --platform=xxxxx 的参数指定镜像架构<br>
可使用 k8s.gcr.io/kube-state-metrics/kube-state-metrics 格式指定私库<br>
可使用 #开头作为注释<br>
![](doc/images.png)
文件提交后，自动进入Github Action构建

### 使用镜像
回到阿里云，镜像仓库，点击任意镜像，可查看镜像状态。(可以改成公开，拉取镜像免登录)
![](doc/开始使用.png)

在国内服务器pull镜像, 例如：<br>
```
docker pull registry.cn-hangzhou.aliyuncs.com/shrimp-images/alpine
```
registry.cn-hangzhou.aliyuncs.com 即 ALIYUN_REGISTRY(阿里云仓库地址)<br>
shrimp-images 即 ALIYUN_NAME_SPACE(阿里云命名空间)<br>
alpine 即 阿里云中显示的镜像名<br>

### 多架构
需要在images.txt中用 --platform=xxxxx手动指定镜像架构
指定后的架构会以前缀的形式放在镜像名字前面
![](doc/多架构.png)

### 镜像重名
程序自动判断是否存在名称相同, 但是属于不同命名空间的情况。
如果存在，会把命名空间作为前缀加在镜像名称前。
例如:
```
xhofe/alist
xiaoyaliu/alist
```
![](doc/镜像重名.png)

### 定时执行
修改/.github/workflows/docker.yaml文件
添加 schedule即可定时执行(此处cron使用UTC时区)
![](doc/定时执行.png)

## 浏览器自动删除镜像 Tag

当 Docker Registry API 返回 401 权限不足时,可以使用浏览器自动化方式删除阿里云镜像 tag。

### 前提条件

1. 安装 Playwright 依赖和浏览器:
```bash
uv sync
uv run playwright install chromium
```

2. 配置环境变量 (创建 `.env` 文件):
```bash
ALIYUN_REGISTRY=registry.cn-beijing.aliyuncs.com
ALIYUN_NAME_SPACE=your-namespace
```

### 使用步骤

#### 1. 保存登录状态

首次使用需要在浏览器中手动登录一次:
```bash
uv run cli.py delete-browser-login
```

命令会打开浏览器访问阿里云控制台,登录成功后在终端按回车键保存状态。

登录状态会保存到 `aliyun_state.json` 文件中。

#### 2. 删除单个 Tag

```bash
# 预览模式 (不实际删除)
uv run cli.py delete-browser-single v1.0.0 --dry-run

# 实际删除 (无头模式)
uv run cli.py delete-browser-single v1.0.0

# 显示浏览器窗口 (调试用)
uv run cli.py delete-browser-single v1.0.0 --show-browser
```

#### 3. 批量删除 Tags

```bash
# 批量删除多个 tags (空格分隔)
uv run cli.py delete-browser-batch "v1.0.0 v1.0.1 v1.0.2"

# 增加操作延迟 (避免触发限制)
uv run cli.py delete-browser-batch "v1.0.0 v1.0.1" --delay 3.0

# 跳过确认提示
uv run cli.py delete-browser-batch "v1.0.0 v1.0.1" --force
```

#### 4. 按正则表达式删除

```bash
# 删除所有匹配正则表达式的 tags
uv run cli.py delete-browser-regex "^test-.*"

# 限制删除数量
uv run cli.py delete-browser-regex "^2025.*" --limit 50

# 预览匹配的 tags
uv run cli.py delete-browser-regex "^v1\\.0\\..*$" --dry-run
```

### 常见问题

#### Q: 登录状态过期怎么办?
重新运行 `uv run cli.py delete-browser-login` 保存新的登录状态。

#### Q: 提示"未找到 tag 元素"?
使用 `--show-browser` 参数查看浏览器操作过程,检查页面结构是否变化。

#### Q: 删除操作很慢?
这是正常的。为避免触发阿里云限制,默认每个操作间隔2秒。可以通过 `--delay` 参数调整。

### 技术细节

- 使用 Playwright 自动化浏览器操作
- 支持无头模式和显示模式
- 保守的元素定位策略,适应页面结构变化
- 自动重试机制,提高稳定性
- 支持批量删除和正则表达式匹配

详细文档请参考: [浏览器删除方案.md](浏览器删除方案.md)
