from typing import Self

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AbstractDynamicChoice(models.Model):
    """Abstract base model for storing dynamic choices."""

    group_name = models.SlugField(
        max_length=100,
        db_index=True,
        help_text=_("The unique identifier for this group of choices (e.g. `Status`, `Priority`)."),
    )
    label = models.CharField(
        max_length=100,
        help_text=_("The human-readable label for the choices (e.g. 'Work In Progress')."),
    )
    value = models.CharField(
        max_length=100,
        help_text=_("The choice value stored in the database (e.g. `in_progress`, `closed`)."),
    )
    ordering = models.IntegerField(
        default=0,
        help_text=_("Control the sort order of choice in dropdowns. Lower numbers appear first."),
    )
    is_system_default = models.BooleanField(
        default=False,
        help_text=_("Indicates if this choice was created by the system during startup."),
    )
    meta_created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True
        ordering = ("group_name", "ordering", "label")

    def __str__(self):
        return f"{self.label} ({self.value})"


class DynamicChoice(AbstractDynamicChoice):
    """The default concrete implementation provided by the package. This model can be
    used as-is for storing dynamic choices.

    This model can be swapped out by setting the `DYNAMIC_CHOICE_MODEL` setting.
    """

    class Meta:
        swappable = "DYNAMIC_CHOICE_MODEL"
        unique_together = ("group_name", "value")
        verbose_name = _("Dynamic Choice")
