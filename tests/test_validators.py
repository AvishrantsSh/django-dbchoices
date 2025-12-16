import pytest
from django.core.exceptions import ValidationError

from dbchoices.utils import get_choice_model
from dbchoices.validators import DynamicChoiceValidator

DynamicChoice = get_choice_model()


@pytest.mark.django_db
class TestDynamicChoiceValidator:
    def test_validator_valid_choice(self, register_status):
        validator = DynamicChoiceValidator(group_name="ticket_status")
        validator("open")

    def test_validator_invalid_choice(self, register_status):
        validator = DynamicChoiceValidator(group_name="ticket_status")
        with pytest.raises(ValidationError) as exc_info:
            validator("invalid_choice")

        assert exc_info.value.code == "invalid_choice_group"
        assert "invalid_choice" in str(exc_info.value)

    def test_validator_empty_value(self, register_status):
        validator = DynamicChoiceValidator(group_name="ticket_status")
        with pytest.raises(ValidationError):
            validator("")

    def test_validator_nonexistent_group(self):
        validator = DynamicChoiceValidator(group_name="nonexistent")
        with pytest.raises(ValidationError):
            validator("any_value")

    def test_validator_with_filters(self):
        DynamicChoice.objects.create(group_name="enum1", name="v1", value="v1", label="l1", is_system_default=True)
        DynamicChoice.objects.create(group_name="enum1", name="v2", value="v2", label="l2", is_system_default=False)

        validator = DynamicChoiceValidator(group_name="enum1", group_filters={"is_system_default": True})

        # Should accept system default
        validator("v1")

        # Should reject custom (not a system default)
        with pytest.raises(ValidationError):
            validator("v2")

    def test_validator_equality(self):
        """Test validator equality comparison"""
        validator1 = DynamicChoiceValidator(group_name="status")
        validator2 = DynamicChoiceValidator(group_name="status")
        validator3 = DynamicChoiceValidator(group_name="other")

        assert validator1 == validator2
        assert validator1 != validator3
