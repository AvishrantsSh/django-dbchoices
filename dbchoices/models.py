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
    name = models.CharField(
        max_length=100,
        help_text=_("The enum-like name for the choice (e.g. `IN_PROGRESS`, `CLOSED`)."),
    )
    label = models.CharField(
        max_length=100,
        help_text=_("The human-readable label for the choices (e.g. 'Work In Progress')."),
    )
    value = models.CharField(
        max_length=100,
        db_index=True,
        help_text=_("The choice value stored in the database (e.g. `in_progress`, `closed`)."),
    )
    ordering = models.IntegerField(
        default=0,
        db_index=True,
        help_text=_("Control the sort order of choices in dropdowns. Lower numbers appear first."),
    )
    is_system_default = models.BooleanField(
        default=False,
        help_text=_("Indicates if this choice was created by the system during startup."),
    )
    meta_created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True
        ordering = ("group_name", "ordering", "label")

    @classmethod
    def get_choices(cls, group_name: str, **group_filters):
        """Fetch all choices for a given `group_name` from the database."""
        return cls.objects.filter(group_name=group_name, **group_filters).order_by("ordering", "value")

    @classmethod
    def _create_choices(cls, choices: list[Self], ignore_conflicts: bool = True) -> list[Self]:
        return cls.objects.bulk_create(choices, ignore_conflicts=ignore_conflicts)

    @classmethod
    def _delete_choices(cls, group_names: list[str], **group_filters) -> None:
        cls.objects.filter(group_name__in=group_names, **group_filters).delete()

    def __str__(self):
        return f"{self.label} ({self.value})"


class DynamicChoice(AbstractDynamicChoice):
    """The default concrete implementation provided by the package. This model can be
    used as-is for storing dynamic choices.

    This model can be swapped out by setting the `DBCHOICE_MODEL` setting.
    """

    class Meta:
        swappable = "DBCHOICE_MODEL"
        unique_together = (("group_name", "name"), ("group_name", "value"))
        verbose_name = _("Dynamic Choice")
