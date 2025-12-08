from django.db import models


class DynamicChoiceField(models.CharField):
    """Extended `CharField` that integrates with ChoiceRegistry for dynamic choices."""


__all__ = ["DynamicChoiceField"]
