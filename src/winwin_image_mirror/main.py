"""WinWin Image Mirror - 主入口

提供命令行接口，将国外 Docker 镜像转存到阿里云私有仓库。
"""

import typer
from dotenv import load_dotenv

from .commands import list, push
from .commands.delete import register as delete_register

load_dotenv()

app = typer.Typer()

list.register(app)
push.register(app)
delete_register(app)

if __name__ == "__main__":
    app()
