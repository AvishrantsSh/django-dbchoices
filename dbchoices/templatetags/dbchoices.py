from django import template

from dbchoices.registry import ChoiceRegistry

register = template.Library()


@register.filter(name="choice_label")
def choice_label(value: str, group_name: str):
    """
    Retrieves the human-readable label for a stored choice value.

    Usage: {{ ticket.status|choice_label:"ticket_status" }}

    If the value is empty or not found, it returns the original value string.
    """
    if value is None or value == "":
        return ""
    return ChoiceRegistry.get_label(group_name, value)


@register.simple_tag(name="get_choice_enum")
def get_choice_enum(group_key: str):
    """
    Injects dynamically generated TextChoices class into the template context.

    Usage:
        {% get_choice_enum "ticket_status" as Status %}
        {% if ticket.status == Status.CLOSED %} ... {% endif %}
    """
    return ChoiceRegistry.get_enum(group_key)
