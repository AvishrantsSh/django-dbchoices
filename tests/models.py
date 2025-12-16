from django.db import models

from dbchoices.fields import DynamicChoiceField
from dbchoices.models import AbstractDynamicChoice


class CustomChoiceModel(AbstractDynamicChoice):
    """A custom choice model for testing purposes"""

    class Meta:
        verbose_name = "Custom Choice"
        verbose_name_plural = "Custom Choices"


class Ticket(models.Model):
    title = models.CharField(max_length=200)
    status = DynamicChoiceField("ticket_status", max_length=50)
    genre = DynamicChoiceField("ticket_genre", group_filters={"is_system_default": True}, null=True, blank=True)

    def __str__(self):
        return self.title
