from rest_framework import serializers

from dbchoices.registry import ChoiceRegistry


class ChoiceFieldMixin:
    """A mixin to provide common functionality for dynamic choice fields."""

    def __init__(self, group_name: str, group_filters: dict | None = None, **kwargs):
        self.group_filters = group_filters or {}
        self.from_label = kwargs.pop("from_label", False)
        super().__init__(choices=group_name, **kwargs)

    @property
    def choices(self):
        """Choices fetched dynamically from the ChoiceRegistry."""
        choices = ChoiceRegistry.get_choices(self._group_name, **self.group_filters)
        if self.from_label:
            return dict((label, label) for _, label in choices)
        return dict(choices)

    @choices.setter
    def choices(self, value):
        # This setter is required by DRF ChoiceField but we don't want to allow
        # external setting of choices, so we only capture the group_name here.
        self._group_name = value

    @property
    def grouped_choices(self):
        # This is used to group choices in HTML representations
        # This value is populated by DRF internally as part of choice setter.
        return self.choices

    @property
    def choice_strings_to_values(self):
        # This is used to map string representations back to their values
        # This value is populated by DRF internally as part of choice setter.
        return {str(label): value for value, label in self.choices.items()}


class DynamicChoiceField(ChoiceFieldMixin, serializers.ChoiceField):
    """
    A DRF ChoiceField that fetches its choices dynamically from the ChoiceRegistry.

    If a custom cache strategy or filters are needed, consider extending this field and overriding
    the `choices` property.
    """


class DynamicMultipleChoiceField(ChoiceFieldMixin, serializers.MultipleChoiceField):
    """
    A DRF MultipleChoiceField that fetches its choices dynamically from the ChoiceRegistry.

    If a custom cache strategy or filters are needed, consider extending this field and overriding
    the `choices` property.
    """
