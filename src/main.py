"""Docker Image Pusher - 主入口

提供命令行接口，将国外 Docker 镜像转存到阿里云私有仓库。
"""
from dotenv import load_dotenv

load_dotenv()

import typer

from .commands import list, push, delete_api
from .commands.delete_browser import login, single, batch, regex

# 创建 Typer 应用
app = typer.Typer()

# 注册命令
list.register(app)
push.register(app)
delete_api.register(app)
login.register(app)
single.register(app)
batch.register(app)
regex.register(app)

if __name__ == "__main__":
    app()
