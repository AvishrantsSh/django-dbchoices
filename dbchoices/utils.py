import json
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings

if TYPE_CHECKING:
    from dbchoices.models import AbstractDynamicChoice


def get_choice_model() -> type["AbstractDynamicChoice"]:
    """Return the initialized dynamic choice model for internal reference.

    This function checks the `DBCHOICE_MODEL` setting to determine
    if a custom choice model has been defined. If not defined, it defaults to the
    built-in `DynamicChoice` model provided by the package.
    """
    model_label = getattr(settings, "DBCHOICE_MODEL", None)

    if model_label is None:
        from dbchoices.models import DynamicChoice

        return DynamicChoice

    return apps.get_model(model_label, require_ready=False)


def generate_cache_key(group_name: str, **filters) -> str:
    """Generate a cache key for storing/retrieving choices."""
    cache_key = f"dbchoice:{group_name}"

    if filters:
        filter_items = tuple((k, str(v)) for k, v in filters.items())
        return cache_key + ":" + json.dumps(sorted(filter_items), separators=(",", ":"))

    return cache_key
