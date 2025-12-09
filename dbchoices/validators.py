from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from dbchoices.registry import ChoiceRegistry


@deconstructible
class DynamicChoiceValidator:
    """
    A reusable Django validator that verifies a value exists in the
    `ChoiceRegistry` for a given group.
    """

    def __init__(self, group_name: str, group_filters: dict | None = None):
        self.group_name = group_name
        self.group_filters = group_filters or {}

    def __call__(self, value):
        # Retrieve the valid values from the registry and validate
        choices = ChoiceRegistry.get_choices(self.group_name, **self.group_filters)
        if not any(str(value) == str(valid_value) for valid_value, _ in choices):
            raise ValidationError(f"'{value}' is not a valid choice.", code="invalid_choice_group")

    def __eq__(self, other):
        return isinstance(other, DynamicChoiceValidator) and self.group_name == other.group_name
