from typing import Any

from django.db import models

from dbchoices.registry import ChoiceRegistry
from dbchoices.validators import DynamicChoiceValidator


class DynamicChoiceField(models.CharField):
    """Extended `CharField` that integrates with ChoiceRegistry for dynamic choices."""

    def __init__(self, group_name: str, group_filters: dict | None = None, *args, **kwargs):
        self.group_name = group_name
        self.group_filters = group_filters or {}
        # Remove choices to ensure dynamic choices are used
        kwargs.pop("choices", None)
        super().__init__(*args, **kwargs)
        self.validators.append(DynamicChoiceValidator(group_name, group_filters=self.group_filters))

    def formfield(self, **kwargs: Any) -> Any:
        self.choices = ChoiceRegistry.get_choices(self.group_name)
        return super().formfield(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["group_name"] = self.group_name
        if "choices" in kwargs:
            del kwargs["choices"]

        return name, path, args, kwargs


__all__ = ["DynamicChoiceField"]
