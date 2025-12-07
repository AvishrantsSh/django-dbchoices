from django.contrib import admin
from django.utils.text import slugify

from dbchoices.utils import get_choice_model


class DynamicChoiceAdmin(admin.ModelAdmin):
    list_display = ("group_name", "value", "label", "choice_name", "ordering", "is_system_default")
    list_filter = ("group_name", "is_system_default")
    search_fields = ("group_name", "value", "label")
    ordering = ("group_name", "ordering")

    def get_readonly_fields(self, request, obj=None):
        # Prevent edits to system defaults
        if obj and obj.is_system_default:
            return ("group_name", "value", "is_system_default")
        return ("is_system_default",)

    @admin.display(description="Enum Choice Name")
    def choice_name(self, obj):
        """Preview of the enum choice name. This is auto-generated and cannot be edited."""
        safe_key = slugify(str(obj.value)).replace("-", "_").upper()
        if not safe_key or safe_key[0].isdigit():
            return f"K_{safe_key}"
        return safe_key


# Auto-register DynamicChoice model if using the default implementation
DynamicChoice = get_choice_model()
if DynamicChoice._meta.app_label == "dbchoices":
    admin.site.register(DynamicChoice, DynamicChoiceAdmin)
