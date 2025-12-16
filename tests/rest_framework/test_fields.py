import pytest
from rest_framework.exceptions import ValidationError

from dbchoices.rest_framework.fields import DynamicChoiceField, DynamicMultipleChoiceField
from dbchoices.utils import get_choice_model
from tests.base import BaseTestCase
from tests.choices import Status
from tests.models import Ticket
from tests.rest_framework import serializers

DynamicChoice = get_choice_model()


@pytest.mark.django_db
class TestDRFDynamicChoiceField(BaseTestCase):
    def test_choices_property(self, register_status):
        field = DynamicChoiceField(group_name="ticket_status")
        assert all(i.value in field.choices for i in Status)

    def test_choices_with_from_label(self, register_status):
        field = DynamicChoiceField(group_name="ticket_status", from_label=True)
        assert all(i.name in field.choices for i in Status)

    def test_validation_for_valid_choice(self, register_status):
        field = DynamicChoiceField(group_name="ticket_status")
        assert field.run_validation("open") == Status.OPEN.value

    def test_validation_for_invalid_choice(self, register_status):
        field = DynamicChoiceField(group_name="ticket_status")
        with pytest.raises(ValidationError) as e:
            field.run_validation("invalid_status")

        assert "invalid_status" in str(e.value)

    def test_validation_new_choice_after_registration(self, register_status):
        field = DynamicChoiceField(group_name="ticket_status")
        with pytest.raises(ValidationError) as e:
            field.run_validation("custom")

        assert "custom" in str(e.value)

        # Create a new choice in the database and re-test
        DynamicChoice.objects.create(
            group_name="ticket_status",
            name="NEW_DEFAULT",
            value="new_default",
            label="New Default",
            is_system_default=False,
        )
        assert field.run_validation("new_default") == "new_default"

    def test_field_with_group_filters(self, register_status):
        # Create a new choice that does not meet the filter criteria
        DynamicChoice.objects.create(
            group_name="ticket_status",
            name="NEW_DEFAULT",
            value="new_default",
            label="New Default",
            is_system_default=False,
        )

        field = DynamicChoiceField(group_name="ticket_status", group_filters={"is_system_default": True})
        assert "open" in field.choices
        assert "new_default" not in field.choices


@pytest.mark.django_db
class TestDRFDynamicMultipleChoiceField:
    def test_choices_property(self, register_status):
        field = DynamicMultipleChoiceField(group_name="ticket_status")
        assert all(i.value in field.choices for i in Status)

    def test_choices_with_from_label(self, register_status):
        field = DynamicMultipleChoiceField(group_name="ticket_status", from_label=True)
        assert all(i.name in field.choices for i in Status)

    def test_validation_for_valid_choice(self, register_status):
        field = DynamicMultipleChoiceField(group_name="ticket_status")
        assert Status.OPEN.value in field.run_validation(["open"])

    def test_validation_for_invalid_choice(self, register_status):
        field = DynamicMultipleChoiceField(group_name="ticket_status")
        with pytest.raises(ValidationError):
            field.run_validation(["invalid_status"])

    def test_validation_for_mixed_choices(self, register_status):
        field = DynamicMultipleChoiceField(group_name="ticket_status")
        with pytest.raises(ValidationError) as e:
            field.run_validation(["open", "invalid_status"])

        assert "invalid_status" in str(e.value)

    def test_validation_new_choice_after_registration(self, register_status):
        field = DynamicMultipleChoiceField(group_name="ticket_status")

        with pytest.raises(ValidationError):
            field.run_validation(["custom"])

        # Create a new choice in the database and re-test
        DynamicChoice.objects.create(
            group_name="ticket_status",
            name="NEW_DEFAULT",
            value="new_default",
            label="New Default",
            is_system_default=False,
        )
        assert "new_default" in field.run_validation(["new_default"])

    def test_field_with_group_filters(self, register_status):
        # Create a new choice that does not meet the filter criteria
        DynamicChoice.objects.create(
            group_name="ticket_status",
            name="NEW_DEFAULT",
            value="new_default",
            label="New Default",
            is_system_default=False,
        )

        field = DynamicMultipleChoiceField(group_name="ticket_status", group_filters={"is_system_default": True})
        assert "open" in field.choices
        assert "custom" not in field.choices


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.parametrize(
    "serializer_class",
    [serializers.TicketSerializer, serializers.TicketSerializerWithField],
)
class TestSerializerIntegration(BaseTestCase):
    def test_serializer_field_serialization(self, register_status, serializer_class):
        ticket = Ticket.objects.create(title="Test", status="open")
        serializer = serializer_class(ticket)
        assert serializer.data["status"] == "open"

    def test_serializer_validation_valid_choice(self, register_status, serializer_class):
        data = {"title": "Test Ticket", "status": "open"}
        serializer = serializer_class(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["status"] == "open"

    def test_serializer_validation_invalid_choice(self, register_status, serializer_class):
        data = {"title": "Test Ticket", "status": "invalid_status"}
        serializer = serializer_class(data=data)
        assert not serializer.is_valid()
        assert "status" in serializer.errors
