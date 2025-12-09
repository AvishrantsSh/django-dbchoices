from rest_framework import serializers

from dbchoices.registry import ChoiceRegistry


class DynamicChoiceField(serializers.ChoiceField):
    """
    A DRF ChoiceField that fetches its choices dynamically from the ChoiceRegistry.

    If a custom cache strategy or filters are needed, consider extending this field and overriding
    the `choices` property.
    """

    def __init__(self, group_name: str, group_filters: dict | None = None, **kwargs):
        self.group_name = group_name
        self.group_filters = group_filters or {}
        self.html_cutoff = kwargs.pop("html_cutoff", self.html_cutoff)
        self.html_cutoff_text = kwargs.pop("html_cutoff_text", self.html_cutoff_text)
        self.allow_blank = kwargs.pop("allow_blank", False)
        super(serializers.ChoiceField, self).__init__(**kwargs)

    @property
    def choices(self):
        """Fetch choices dynamically from the ChoiceRegistry."""
        return dict(ChoiceRegistry.get_choices(self.group_name, **self.group_filters))

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
