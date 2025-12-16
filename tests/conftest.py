import django
import pytest

from dbchoices.registry import ChoiceRegistry
from tests.choices import Genre, Status


def pytest_configure():
    """Configure pytest settings"""
    django.setup()


@pytest.fixture
def register_status():
    """Register ticket status choices in the registry"""
    ChoiceRegistry.register_enum(Status, group_name="ticket_status")
    ChoiceRegistry.sync_defaults(group_names=["ticket_status"])


@pytest.fixture
def register_ticket_genre():
    """Register ticket genre choices in the registry"""
    ChoiceRegistry.register_enum(Genre, group_name="ticket_genre")
    ChoiceRegistry.sync_defaults(group_names=["ticket_genre"])
