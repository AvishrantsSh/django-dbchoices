from django.core.cache import cache


class BaseTestCase:
    """Base test case with common setup for tests."""

    def teardown_method(self, method):
        # Clear cache after each test
        cache.clear()
