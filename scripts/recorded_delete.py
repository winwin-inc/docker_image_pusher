import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="../data/aliyun_state.json")
    page = context.new_page()
    page.goto("https://cr.console.aliyun.com/repository/cn-beijing/winwin/tool/images")
    page.get_by_role("button", name="第2页，共8页").click()
    page.get_by_text("删除").nth(1).click()
    page.get_by_text("确定删除该版本的镜像").click()
    page.get_by_role("button", name="确定").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
