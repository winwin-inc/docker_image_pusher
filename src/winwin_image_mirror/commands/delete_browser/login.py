"""浏览器登录命令模块

实现保存浏览器登录状态的功能。
"""

import os

import typer

from ...browser.state import save_login_state


def register(app: typer.Typer):
    """注册 delete-browser-login 命令

    Args:
        app: Typer 应用实例
    """

    @app.command(name="delete-browser-login")
    def delete_browser_login():
        """保存浏览器登录状态

        打开浏览器访问阿里云控制台，用户手动登录后保存状态到本地文件。
        保存的状态文件将用于后续的浏览器自动化删除操作。

        示例:
            cli.py delete-browser-login
        """
        # 默认登录状态文件路径
        storage_state_path = os.getenv("ALIYUN_STATE_PATH", "data/aliyun_state.json")

        save_login_state(storage_state_path)
