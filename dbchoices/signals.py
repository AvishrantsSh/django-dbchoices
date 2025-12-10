from dbchoices.registry import ChoiceRegistry
from dbchoices.utils import get_choice_model

ChoiceModel = get_choice_model()


def invalidate_choice_cache(sender, instance, **kwargs):
    """Signal handler to invalidate choice cache on model save/delete."""
    if isinstance(instance, ChoiceModel):
        ChoiceRegistry.invalidate_cache(instance.group_name)
