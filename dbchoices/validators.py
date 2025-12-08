from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from dbchoices.registry import ChoiceRegistry


@deconstructible
class DynamicChoiceValidator:
    """
    A reusable Django validator that verifies a value exists in the
    `ChoiceRegistry` for a given group.
    """

    def __init__(self, group_key: str):
        self.group_key = group_key

    def __call__(self, value):
        # Retrieve the valid values from the registry and validate
        choices = ChoiceRegistry.get_choices(self.group_key)
        if not any(str(value) == str(valid_value) for valid_value, _ in choices):
            raise ValidationError(f"'{value}' is not a valid choice.", code="invalid_choice_group")

    def __eq__(self, other):
        return isinstance(other, DynamicChoiceValidator) and self.group_key == other.group_key
