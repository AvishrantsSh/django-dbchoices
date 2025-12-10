from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_delete, post_save


class DbchoicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dbchoices"

    def ready(self):
        if getattr(settings, "DBCHOICES_AUTO_INVALIDATE_CACHE", True):
            # Register signal handlers to invalidate choice cache on model changes
            from dbchoices.signals import invalidate_choice_cache
            from dbchoices.utils import get_choice_model

            ChoiceModel = get_choice_model()
            post_save.connect(invalidate_choice_cache, sender=ChoiceModel, dispatch_uid="dbchoices_invalidate_save")
            post_delete.connect(invalidate_choice_cache, sender=ChoiceModel, dispatch_uid="dbchoices_invalidate_delete")
