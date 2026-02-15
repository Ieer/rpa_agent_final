from __future__ import annotations

import time
from urllib.parse import quote_plus

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def open_notepad() -> None:
    import pyautogui

    pyautogui.press("win")
    time.sleep(3)
    pyautogui.typewrite("notepad")
    pyautogui.press("enter")


def type_text(text: str) -> None:
    import pyautogui

    pyautogui.typewrite(text, interval=0.05)


def baidu_search(keyword: str) -> str:
    if sync_playwright is None:
        raise RuntimeError("playwright 未安裝，請先執行: pip install playwright && playwright install chromium")

    url = f"https://www.baidu.com/s?tn=news&word={quote_plus(keyword)}"
    top_news: list[dict[str, str]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1200)

        cards = page.query_selector_all("div.result, div.c-container")
        for card in cards:
            title_el = card.query_selector("h3 a, h3, a")
            if not title_el:
                continue

            title = (title_el.inner_text() or "").strip()
            link = (title_el.get_attribute("href") or "").strip()
            summary_el = card.query_selector(".c-summary, .c-font-normal")
            summary = (summary_el.inner_text() or "").strip() if summary_el else ""

            if not title:
                continue

            top_news.append(
                {
                    "title": title,
                    "url": link,
                    "summary": summary,
                }
            )

            if len(top_news) >= 10:
                break

        browser.close()

    return {
        "query": keyword,
        "source": "baidu_news",
        "top_news": top_news,
    } # type: ignore


RPA_REGISTRY = {
    "open_notepad": {
        "func": open_notepad,
        "desc": "打開系統記事本",
        "params": [],
    },
    "type_text": {
        "func": type_text,
        "desc": "向目前視窗輸入文字",
        "params": ["text"],
    },
    "baidu_search": {
        "func": baidu_search,
        "desc": "百度新聞搜尋 Top 10",
        "params": ["keyword"],
    },
}
