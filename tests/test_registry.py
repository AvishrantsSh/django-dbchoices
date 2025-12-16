from enum import Enum
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import models

from dbchoices.registry import ChoiceRegistry
from dbchoices.utils import generate_cache_key, get_choice_model
from tests.base import BaseTestCase
from tests.choices import Status

DynamicChoice = get_choice_model()


@pytest.mark.django_db
class TestChoiceRegistry(BaseTestCase):
    def test_register_defaults_normalizes_types(self):
        choices = [("HIGH", 1, "High Priority"), ("LOW", 2, "Low Priority")]
        ChoiceRegistry.register_defaults("numbers", choices)
        for registered in ChoiceRegistry._defaults["numbers"]:
            assert isinstance(registered[0], str), "Choice name should be str"
            assert isinstance(registered[1], str), "Choice value should be str"
            assert isinstance(registered[2], str), "Choice label should be str"

    def test_register_defaults_duplicate_name(self):
        choices = [("HIGH", 1, "High Priority"), ("HIGH", 2, "Low Priority")]
        with pytest.raises(ValueError, match="Duplicate choice name"):
            ChoiceRegistry.register_defaults("status", choices)

    def test_register_defaults_duplicate_value(self):
        choices = [("HIGH", 1, "High Priority"), ("LOW", 1, "Low Priority")]
        with pytest.raises(ValueError, match="Duplicate choice value"):
            ChoiceRegistry.register_defaults("status", choices)

    def test_register_defaults_invalid_tuple_length(self):
        invalid_choices = [("ONLY_NAME",), ("NAME", "VALUE")]

        with pytest.raises(ValueError, match="Invalid choice format"):
            ChoiceRegistry.register_defaults("status", invalid_choices)

    def test_register_defaults_slug_warning(self, caplog):
        choices = [("invalid-choice", "invalid-choice", "Invalid Choice")]

        with caplog.at_level("WARNING"):
            ChoiceRegistry.register_defaults("status", choices)

        assert any("not a valid Python identifier" in record.message for record in caplog.records)

    def test_register_enum(self):
        class StatusEnum(Enum):
            OPEN = "open"
            CLOSED = "closed"

        ChoiceRegistry.register_enum(StatusEnum)
        registered_choices = ChoiceRegistry._defaults["StatusEnum"]
        assert registered_choices == [("OPEN", "open", "OPEN"), ("CLOSED", "closed", "CLOSED")]

    def test_register_enum_with_labels(self):
        class StatusChoices(models.TextChoices):
            OPEN = "open", "Open"
            CLOSED = "closed", "Closed"

        ChoiceRegistry.register_enum(StatusChoices)
        registered_choices = ChoiceRegistry._defaults["StatusChoices"]
        assert registered_choices == [("OPEN", "open", "Open"), ("CLOSED", "closed", "Closed")]

    def test_get_choices_from_database(self, register_status):
        choices = ChoiceRegistry.get_choices("ticket_status")
        assert len(choices)

    def test_get_choices_case_sensitivity(self, register_status):
        choices_upper = ChoiceRegistry.get_choices("TICKET_STATUS")
        assert len(choices_upper) == 0, "Should be case-sensitive and return no choices"

    def test_get_choice_accesses_database_only_once(self):
        with patch.object(DynamicChoice.objects, "filter", wraps=DynamicChoice.objects.filter) as mock_filter:
            ChoiceRegistry.get_choices("ticket_status")
            assert mock_filter.call_count == 1, "Database should be accessed once"

            mock_filter.reset_mock()
            ChoiceRegistry.get_choices("ticket_status")
            assert mock_filter.call_count == 0, "Database should not be accessed again due to caching"

    def test_get_choices_empty_group(self):
        choices = ChoiceRegistry.get_choices("nonexistent")
        assert choices == []

    def test_get_label_finds_match(self, register_status):
        """Test get_label returns correct label"""
        label = ChoiceRegistry.get_label("ticket_status", "open")
        assert label == "OPEN"

    def test_get_label_no_match(self, register_status):
        """Test get_label returns None when no match"""
        label = ChoiceRegistry.get_label("ticket_status", "nonexistent")
        assert label is None

    def test_get_enum_basic(self, register_status):
        StatusEnum = ChoiceRegistry.get_enum("ticket_status")
        assert issubclass(StatusEnum, models.TextChoices)
        assert StatusEnum._member_names_ == Status._member_names_

    def test_get_enum_caches_result(self, register_status):
        enum1 = ChoiceRegistry.get_enum("ticket_status")
        enum2 = ChoiceRegistry.get_enum("ticket_status")
        assert enum1 is enum2

    def test_get_enum_only_system_defaults(self, register_status):
        """Test get_enum only includes system defaults"""
        DynamicChoice.objects.create(
            group_name="status",
            value="system",
            label="System",
            is_system_default=True,
        )
        DynamicChoice.objects.create(
            group_name="ticket_status",
            name="NEW_DEFAULT",
            value="new_default",
            label="New Default",
            is_system_default=False,
        )

        ChoiceRegistry.register_defaults("status", [("system", "System")])
        ChoiceRegistry.sync_defaults(["status"])

        StatusEnum = ChoiceRegistry.get_enum("status")

        assert hasattr(StatusEnum, "SYSTEM")
        assert not hasattr(StatusEnum, "CUSTOM")

    def test_get_enum_empty_group_raises_error(self):
        with pytest.raises(ValueError, match="No choices found for group"):
            ChoiceRegistry.get_enum("nonexistent")

    def test_sync_defaults_creates_choices(self, register_status):
        db_choices = DynamicChoice.objects.filter(group_name="ticket_status")
        assert db_choices.count() == 4
        assert all(c.is_system_default for c in db_choices)

    def test_sync_defaults_preserves_ordering(self, register_status):
        queryset = DynamicChoice.objects.filter(group_name="ticket_status").order_by("ordering")
        db_choices = tuple(queryset.values_list("value", flat=True))
        assert db_choices == ("open", "in_progress", "resolved", "closed")

    def test_sync_defaults_recreate_defaults_true(self, register_status):
        ChoiceRegistry.register_defaults("ticket_status", [("CUSTOM", "custom", "Custom")])
        ChoiceRegistry.sync_defaults(recreate_defaults=True)
        assert DynamicChoice.objects.filter(group_name="ticket_status").count() == 1

    def test_sync_defaults_recreate_defaults_false(self, register_status):
        ChoiceRegistry.register_defaults("ticket_status", [("CUSTOM", "custom", "Custom")])
        ChoiceRegistry.sync_defaults(recreate_defaults=False)
        assert DynamicChoice.objects.filter(group_name="ticket_status").count() == 5

    def test_sync_defaults_recreate_defaults_preserves_custom(self, register_status):
        # Add a custom choice
        DynamicChoice.objects.create(
            group_name="ticket_status",
            name="NEW_DEFAULT",
            value="new_default",
            label="New Default",
            is_system_default=False,
        )

        ChoiceRegistry.register_defaults("ticket_status", [("CUSTOM", "custom", "Custom")])
        ChoiceRegistry.sync_defaults(recreate_defaults=True)

        assert DynamicChoice.objects.filter(group_name="ticket_status").count() == 2
        assert DynamicChoice.objects.filter(group_name="ticket_status", name="NEW_DEFAULT").exists()

    def test_sync_defaults_recreate_all_true(self, register_status):
        # Add a custom choice
        DynamicChoice.objects.create(
            group_name="ticket_status",
            name="NEW_DEFAULT",
            value="new_default",
            label="New Default",
            is_system_default=False,
        )

        ChoiceRegistry.register_defaults("ticket_status", [("CUSTOM", "custom", "Custom")])
        ChoiceRegistry.sync_defaults(recreate_all=True)

        assert DynamicChoice.objects.filter(group_name="ticket_status").count() == 1
        assert not DynamicChoice.objects.filter(group_name="ticket_status", name="NEW_DEFAULT").exists()

    def test_invalidate_cache(self, register_status):
        """Test invalidate_cache clears cache"""
        ChoiceRegistry.get_choices("ticket_status")

        cache_key = generate_cache_key("ticket_status")
        assert cache.get(cache_key) is not None, "Cache should be available before invalidation"

        ChoiceRegistry.invalidate_cache("ticket_status")
        assert cache.get(cache_key) is None, "Cache should be cleared after invalidation"

    def test_invalidate_cache_with_filters(self, register_status):
        DynamicChoice.objects.create(
            group_name="ticket_status",
            name="NEW_DEFAULT",
            value="new_default",
            label="New Default",
            is_system_default=False,
        )

        ChoiceRegistry.get_choices("ticket_status", is_system_default=True)

        cache_key = generate_cache_key("ticket_status", is_system_default=True)
        assert cache.get(cache_key) is not None, "Cache should be available before invalidation"

        ChoiceRegistry.invalidate_cache("ticket_status")
        assert cache.get(cache_key) is not None, "Cache with filters should remain if cache invalidated without filters"

        ChoiceRegistry.invalidate_cache("ticket_status", is_system_default=True)
        assert cache.get(cache_key) is None, "Cache with filters should be cleared after invalidation with filters"
