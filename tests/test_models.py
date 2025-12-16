import pytest
from django.db import IntegrityError

from dbchoices.utils import get_choice_model
from tests.base import BaseTestCase

DynamicChoice = get_choice_model()


@pytest.mark.django_db
class TestDynamicChoiceModel(BaseTestCase):
    def test_unique_constraint(self):
        DynamicChoice.objects.create(group_name="enum1", name="v1", value="v1", label="l1")
        # Attempting to create another choice with same group_name and value should fail
        with pytest.raises(IntegrityError):
            DynamicChoice.objects.create(group_name="enum1", name="v2", value="v1", label="l2")

    def test_different_groups_same_value(self):
        choice1 = DynamicChoice.objects.create(group_name="enum1", name="v1", value="v1", label="l1_old")
        choice2 = DynamicChoice.objects.create(group_name="enum2", name="v1", value="v1", label="l1_new")
        assert choice1.group_name != choice2.group_name
        assert choice1.value == choice2.value

    def test_get_choices_classmethod(self):
        DynamicChoice.objects.create(group_name="enum1", name="v1", value="v1", label="l1", ordering=1)
        DynamicChoice.objects.create(group_name="enum2", name="v1", value="v1", label="l1", ordering=1)
        DynamicChoice.objects.create(group_name="enum2", name="v2", value="v2", label="l2", ordering=2)

        status_choices = DynamicChoice.get_choices("enum2")
        assert tuple(status_choices.values_list("value", "label")) == (("v1", "l1"), ("v2", "l2"))

    def test_get_choices_with_filters(self):
        DynamicChoice.objects.create(group_name="enum1", name="v1", value="v1", label="l1", is_system_default=True)
        DynamicChoice.objects.create(group_name="enum1", name="v2", value="v2", label="l2", is_system_default=False)

        system_defaults = DynamicChoice.get_choices("enum1", is_system_default=True)
        assert system_defaults.count() == 1
        assert system_defaults.first().name == "v1"

    def test_create_choices_bulk(self):
        """Test _create_choices bulk creation"""
        choices = [
            DynamicChoice(group_name="enum1", name=f"S{i}", value=f"status_{i}", label=f"Status {i}") for i in range(5)
        ]

        created = DynamicChoice._create_choices(choices)
        assert len(created) == 5
        assert DynamicChoice.objects.filter(group_name="enum1").count() == 5

    def test_create_choices_ignore_conflicts(self):
        """Test _create_choices with ignore_conflicts=True"""
        DynamicChoice.objects.create(group_name="enum1", name="v1", value="v1", label="l1_old")
        choices = [
            DynamicChoice(group_name="enum1", name="v1", value="v1", label="l1_new"),
            DynamicChoice(group_name="enum1", name="v2", value="v2", label="l2_new"),
        ]

        # Should not raise error with ignore_conflicts=True
        DynamicChoice._create_choices(choices, ignore_conflicts=True)
        existing = DynamicChoice.objects.get(group_name="enum1", name="v1")
        assert existing.label == "l1_old"

    def test_delete_choices(self):
        """Test _delete_choices classmethod"""
        DynamicChoice.objects.create(group_name="enum1", name="v1", value="v1", label="l1", is_system_default=True)
        DynamicChoice.objects.create(group_name="enum1", name="v2", value="v2", label="l2", is_system_default=False)
        DynamicChoice.objects.create(group_name="enum2", name="v1", value="v1", label="l1", is_system_default=True)

        DynamicChoice._delete_choices(["enum1"])
        assert DynamicChoice.objects.filter(group_name="enum1").count() == 0
        assert DynamicChoice.objects.filter(group_name="enum2").count() == 1

    def test_delete_choices_with_filters(self):
        """Test _delete_choices with filters"""
        DynamicChoice.objects.create(group_name="enum1", name="v1", value="v1", label="l1", is_system_default=True)
        DynamicChoice.objects.create(group_name="enum1", name="v2", value="v2", label="l2", is_system_default=False)
        DynamicChoice.objects.create(group_name="enum2", name="v1", value="v1", label="l1", is_system_default=True)

        DynamicChoice._delete_choices(["enum1"], is_system_default=True)
        assert DynamicChoice.objects.filter(group_name="enum1").count() == 1
        assert DynamicChoice.objects.filter(group_name="enum2").count() == 1
