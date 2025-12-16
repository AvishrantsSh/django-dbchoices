import pytest
from django.core.exceptions import ValidationError

from dbchoices.fields import DynamicChoiceField
from dbchoices.utils import get_choice_model
from dbchoices.validators import DynamicChoiceValidator
from tests.base import BaseTestCase
from tests.models import Ticket

DynamicChoice = get_choice_model()


@pytest.mark.django_db
class TestDynamicChoiceField(BaseTestCase):
    def test_field_removes_static_choices(self):
        field = DynamicChoiceField(group_name="my_status", choices=[("a", "A"), ("b", "B")])
        assert field.choices is None

    def test_field_adds_validator(self):
        field = DynamicChoiceField(group_name="my_status")
        assert any(isinstance(v, DynamicChoiceValidator) for v in field.validators)

    def test_formfield_gets_dynamic_choices(self, register_status):
        field = DynamicChoiceField(group_name="ticket_status")
        field.formfield()  # Force the choices to be set
        assert len(field.choices) == 4

    def test_model_field_validation_valid(self, register_status):
        ticket = Ticket(title="Test", status="open")
        ticket.full_clean()

    def test_model_field_validation_invalid(self, register_status):
        ticket = Ticket(title="Test", status="invalid_status")

        with pytest.raises(ValidationError) as exc_info:
            ticket.full_clean()

        assert "status" in exc_info.value.error_dict

    def test_model_field_group_filters_and_valid_choice(self, register_status, register_ticket_genre):
        DynamicChoice.objects.create(group_name="ticket_genre", value="kids", label="Kids")
        ticket = Ticket(title="Test", genre="comedy", status="open")
        ticket.full_clean()

    def test_model_field_group_filters_and_invalid_choice(self, register_status, register_ticket_genre):
        DynamicChoice.objects.create(group_name="ticket_genre", value="kids", label="Kids")
        ticket = Ticket(title="Test", genre="kids", status="open")
        with pytest.raises(ValidationError) as exc_info:
            ticket.full_clean()

        assert "genre" in exc_info.value.error_dict, "Expected 'genre' to be in error dict"
        assert "status" not in exc_info.value.error_dict, "Did not expect 'status' to be in error dict"
