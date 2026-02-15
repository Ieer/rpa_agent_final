import unittest
from unittest.mock import patch

from core import registry


class _FakeElement:
    def __init__(self, text="", href="", summary=""):
        self._text = text
        self._href = href
        self._summary = summary

    def inner_text(self):
        return self._text

    def get_attribute(self, name):
        if name == "href":
            return self._href
        return None

    def query_selector(self, selector):
        if selector in ("h3 a, h3, a", "h3 a", "h3", "a"):
            return _FakeElement(text=self._text, href=self._href)
        if selector in (".c-summary, .c-font-normal", ".c-summary", ".c-font-normal"):
            return _FakeElement(text=self._summary)
        return None


class _FakeCard:
    def __init__(self, idx):
        self.idx = idx

    def query_selector(self, selector):
        if selector == "h3 a, h3, a":
            return _FakeElement(text=f"新聞{self.idx}", href=f"https://example.com/{self.idx}")
        if selector == ".c-summary, .c-font-normal":
            return _FakeElement(text=f"摘要{self.idx}")
        return None


class _FakePage:
    def goto(self, *_args, **_kwargs):
        return None

    def wait_for_timeout(self, *_args, **_kwargs):
        return None

    def query_selector_all(self, _selector):
        return [_FakeCard(i) for i in range(1, 13)]


class _FakeBrowser:
    def new_page(self):
        return _FakePage()

    def close(self):
        return None


class _FakePlaywright:
    class chromium:
        @staticmethod
        def launch(headless=True):
            _ = headless
            return _FakeBrowser()


class _FakeContextManager:
    def __enter__(self):
        return _FakePlaywright()

    def __exit__(self, exc_type, exc, tb):
        _ = exc_type, exc, tb
        return False


class TestRegistry(unittest.TestCase):
    def test_baidu_search_top10(self):
        with patch("core.registry.sync_playwright", return_value=_FakeContextManager()):
            result = registry.baidu_search("台灣新聞")

        self.assertEqual(result["source"], "baidu_news")
        self.assertEqual(result["query"], "台灣新聞")
        self.assertEqual(len(result["top_news"]), 10)
        self.assertEqual(result["top_news"][0]["title"], "新聞1")


if __name__ == "__main__":
    unittest.main()
