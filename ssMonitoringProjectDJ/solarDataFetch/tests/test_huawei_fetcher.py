from django.test import TestCase
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher

class HuaweiLoginTest(TestCase):
    def test_login_real_request(self):
        fetcher = HuaweiFetcher()
        try:
            token = fetcher.login()
            print("Login successful! xsrf-token:", token)
            self.assertIsNotNone(token)
        except Exception as e:
            self.fail(f"Login failed: {e}")

class HuaweiGeneracionSistemaDiaTest(TestCase):
    def test_fetch_huawei_generacion_sistema_dia(self):
        from datetime import datetime, timezone, timedelta
        fetcher = HuaweiFetcher()
        try:
            token = "n-pd7s876obu8bpe6ovz45ipjvo8unk5pj4afvel9eg8ldherts5kaqoo4g55jipmq1jpc7xeq8bdehe5jfw5gtgs6mmo4hc3urygbgb8bhe6kftvsul87aq9cuo07vyak"
            yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            collect_time = int(yesterday.timestamp() * 1000)
            response = fetcher.fetch_huawei_generacion_sistema_dia(
                batch_number=1,
                collect_time=collect_time,
                token=token
            )
            print("Huawei API response:", response)
            self.assertIn('success', response)
        except Exception as e:
            self.fail(f"Fetching Huawei generation data failed: {e}")
