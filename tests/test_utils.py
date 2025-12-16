from django.test import override_settings

from dbchoices.utils import generate_cache_key, get_choice_model
from tests.base import BaseTestCase
from tests.models import CustomChoiceModel

DynamicChoice = get_choice_model()


class TestGetChoiceModel:
    @override_settings(DBCHOICE_MODEL=None)
    def test_get_choice_model_default(self):
        model = get_choice_model()

        assert model is DynamicChoice

    @override_settings(DBCHOICE_MODEL="tests.CustomChoiceModel")
    def test_get_choice_model_custom_definition(self):
        model = get_choice_model()

        assert model is not DynamicChoice
        assert model is CustomChoiceModel


class TestGenerateCacheKey(BaseTestCase):
    def test_generate_cache_key_basic(self):
        key = generate_cache_key("status")
        assert key == "dbchoice:status"

    def test_generate_cache_key_with_single_filter(self):
        key = generate_cache_key("status", is_active=True)
        assert key == 'dbchoice:status:[["is_active","True"]]'

    def test_generate_cache_key_with_multiple_filters(self):
        key = generate_cache_key("status", is_active=True, category="admin")
        assert key == 'dbchoice:status:[["category","admin"],["is_active","True"]]'

    def test_generate_cache_key_order_consistency(self):
        key1 = generate_cache_key("status", is_active=True, category="admin")
        key2 = generate_cache_key("status", category="admin", is_active=True)
        assert key1 == key2

    def test_generate_cache_key_case_sensitivity(self):
        key1 = generate_cache_key("Status", is_active=True)
        key2 = generate_cache_key("status", is_active=True)
        assert key1 != key2

    def test_generate_cache_key_with_different_values(self):
        key1 = generate_cache_key("status", is_active=True)
        key2 = generate_cache_key("status", is_active=False)
        assert key1 != key2
