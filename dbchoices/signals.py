def invalidate_choice_cache(sender, instance, **kwargs):
    """Signal handler to invalidate choice cache on model save/delete."""
    from dbchoices.registry import ChoiceRegistry

    ChoiceRegistry.invalidate_cache(instance.group_name)
