"""WinWin Image Mirror - 主入口

提供命令行接口，将国外 Docker 镜像转存到阿里云私有仓库。
"""

import typer
from dotenv import load_dotenv

from .commands import delete_api, list, push
from .commands.delete_browser import batch, login, regex, single

load_dotenv()
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
