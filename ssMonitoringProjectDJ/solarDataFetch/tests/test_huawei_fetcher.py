from django.test import TestCase
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher

class HuaweiFetcherTest(TestCase):
    def test_login_real_request(self):
        fetcher = HuaweiFetcher()
        try:
            token = fetcher.login()
            print("Login successful! xsrf-token:", token)
            self.assertIsNotNone(token)
        except Exception as e:
            self.fail(f"Login failed: {e}")
