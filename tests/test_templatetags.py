import pytest
from django.template import Context, Template

from dbchoices.utils import get_choice_model
from tests.base import BaseTestCase

DynamicChoice = get_choice_model()


@pytest.mark.django_db
class TestChoiceLabelFilter(BaseTestCase):
    @pytest.mark.parametrize(
        "status,expected_label",
        (("open", "OPEN"), ("closed", "CLOSED"), ("", ""), (None, ""), ("na", "na")),
    )
    def test_choice_label_filter(self, register_status, status, expected_label):
        template = Template("""
            {% load dbchoices %}
            {{ status|choice_label:'ticket_status' }}
        """)

        context = Context({"status": status})
        assert template.render(context).strip() == expected_label


@pytest.mark.django_db
class TestGetChoiceEnumTag:
    def test_get_choice_enum_value(self, register_status):
        template = Template("""
            {% load dbchoices %}
            {% get_choice_enum "ticket_status" as StatusEnum %}
            {{ StatusEnum.OPEN.value }}
        """)

        context = Context({})
        assert template.render(context).strip() == "open"

    def test_get_choice_enum_label(self, register_status):
        template = Template("""
            {% load dbchoices %}
            {% get_choice_enum "ticket_status" as StatusEnum %}
            {{ StatusEnum.OPEN.label }}
        """)

        context = Context({})
        assert template.render(context).strip() == "OPEN"

    def test_get_choice_nonexistent_group(self):
        template = Template("""
            {% load dbchoices %}
            {% get_choice_enum "nonexistent" as Enum %}
        """)
        context = Context({})
        with pytest.raises(ValueError):
            template.render(context)

    def test_get_choice_with_nonexistent_default(self, register_status):
        DynamicChoice.objects.create(group_name="ticket_status", name="CUSTOM", value="custom", label="Custom")
        template = Template("""
            {% load dbchoices %}
            {% get_choice_enum "ticket_status" as StatusEnum %}
            {{ StatusEnum.CUSTOM }}
        """)

        context = Context({})
        assert template.render(context).strip() == ""

    def test_get_choice_multiple_enums(self, register_status, register_ticket_genre):
        template = Template("""
            {% load dbchoices %}
            {% get_choice_enum "ticket_status" as StatusEnum %}
            {% get_choice_enum "ticket_genre" as GenreEnum %}
            {{ StatusEnum.OPEN }}-{{ GenreEnum.COMEDY }}
        """)

        context = Context({})
        rendered = template.render(context).strip()
        assert "open" in rendered, "Expected StatusEnum.OPEN to be in output"
        assert "comedy" in rendered, "Expected GenreEnum.COMEDY to be in output"
