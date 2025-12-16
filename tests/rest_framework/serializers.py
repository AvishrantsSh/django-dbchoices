from rest_framework import serializers

from dbchoices.rest_framework.fields import DynamicChoiceField
from tests.models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    """Basic Ticket serializer using DRF"""

    class Meta:
        model = Ticket
        fields = ("id", "title", "status", "genre")


class TicketSerializerWithField(serializers.ModelSerializer):
    status = DynamicChoiceField(group_name="ticket_status")
    genre = DynamicChoiceField(
        group_name="ticket_genre",
        group_filters={"is_system_default": True},
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Ticket
        fields = ("id", "title", "status", "genre")
