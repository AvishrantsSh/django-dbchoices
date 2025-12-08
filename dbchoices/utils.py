from django.apps import apps
from django.conf import settings

from dbchoices.models import AbstractDynamicChoice, DynamicChoice


def get_choice_model() -> type[AbstractDynamicChoice]:
    """Return the initialized dynamic choice model for internal reference.

    This function checks the `DYNAMIC_CHOICE_MODEL` setting to determine
    if a custom choice model has been defined. If not defined, it defaults to the
    built-in `DynamicChoice` model provided by the package.
    """
    model_label = getattr(settings, "DYNAMIC_CHOICE_MODEL", None)

    if model_label is None:
        return DynamicChoice

    return apps.get_model(model_label, require_ready=False)
