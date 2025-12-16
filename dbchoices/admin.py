from django.contrib import admin

from dbchoices.utils import get_choice_model


class DynamicChoiceAdmin(admin.ModelAdmin):
    list_display = ("group_name", "name", "value", "label", "ordering", "is_system_default")
    list_filter = ("group_name", "is_system_default")
    search_fields = ("group_name", "value", "label")
    ordering = ("group_name", "ordering")

    def get_readonly_fields(self, request, obj=None):
        # Prevent edits to system defaults
        if obj and obj.is_system_default:
            return ("group_name", "value", "is_system_default")
        return ("is_system_default",)


# Auto-register DynamicChoice model if using the default implementation
DynamicChoice = get_choice_model()
if DynamicChoice._meta.app_label == "dbchoices":
    admin.site.register(DynamicChoice, DynamicChoiceAdmin)
