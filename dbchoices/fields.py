from functools import partialmethod
from typing import Any

from django.db import models
from django.utils.choices import BlankChoiceIterator

from dbchoices.registry import ChoiceRegistry
from dbchoices.validators import DynamicChoiceValidator

BLANK_CHOICE_DASH = (("", "---------"),)


class DynamicChoiceField(models.CharField):
    """Extended `CharField` that integrates with ChoiceRegistry for dynamic choices."""

    def __init__(self, group_name: str, group_filters: dict | None = None, *args, **kwargs):
        self.group_name = group_name
        self.group_filters = group_filters or {}
        # Remove choices to ensure dynamic choices are used
        kwargs.pop("choices", None)
        super().__init__(*args, **kwargs)
        self.validators.append(DynamicChoiceValidator(group_name, group_filters=self.group_filters))

    @property
    def flatchoices(self):
        return ChoiceRegistry.get_choices(self.group_name, **self.group_filters)

    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH, *args, **kwargs):
        if include_blank:
            return BlankChoiceIterator(self.flatchoices, blank_choice)
        return self.flatchoices

    def contribute_to_class(self, cls: models.Model, name: str, private_only=False) -> None:
        super().contribute_to_class(cls, name, private_only)
        # Extend get_%s_display method to the model with dynamic choices
        method_name = f"get_{self.name}_display"
        if method_name not in cls.__dict__:
            setattr(cls, method_name, partialmethod(cls._get_FIELD_display, field=self))

    def formfield(self, **kwargs: Any) -> Any:
        self.choices = ChoiceRegistry.get_choices(self.group_name, **self.group_filters)
        return super().formfield(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["group_name"] = self.group_name
        if "choices" in kwargs:
            del kwargs["choices"]

        return name, path, args, kwargs


__all__ = ["DynamicChoiceField"]
