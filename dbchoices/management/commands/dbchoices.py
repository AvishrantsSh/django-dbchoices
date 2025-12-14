from django.core.management.base import BaseCommand

from dbchoices.registry import ChoiceRegistry


class Command(BaseCommand):
    help = "Synchronize dynamic choice defaults from code to the database."

    def add_arguments(self, parser):
        action_group = parser.add_mutually_exclusive_group(required=True)
        action_group.add_argument(
            "--sync",
            nargs="*",
            help="Synchronize default choices from code definitions to the database.",
        )
        action_group.add_argument(
            "-l",
            "--list",
            action="store_true",
            help="List all choices currently registered in the Python code.",
        )
        action_group.add_argument(
            "--invalidate",
            help="Specify a group name to invalidate its cache.",
        )

        # Sync optional arguments
        parser.add_argument(
            "--recreate-defaults",
            action="store_true",
            help="Recreate all default choices from code definitions.",
        )
        parser.add_argument(
            "--recreate-all",
            action="store_true",
            help="Recreate all choices, including non-defaults, from code definitions.",
        )

    def handle(self, *args, **options):
        if options["list"]:
            self._list_choices()
        elif options["invalidate"] is not None:
            self._invalidate_cache(options["invalidate"])
        elif options["sync"] is not None:
            self._sync_defaults(
                group_names=options["sync"] or None,  # Pass None if no specific groups are provided
                recreate_defaults=options["recreate_defaults"],
                recreate_all=options["recreate_all"],
            )

    def _list_choices(self):
        """List all choices currently registered in the Python code."""
        for group_name, choices in ChoiceRegistry._defaults.items():
            self.stdout.write(f"Group: {group_name}")
            for name, value, label in choices:
                self.stdout.write(f"  Name: {name}")
                self.stdout.write(f"    Value: {value}")
                self.stdout.write(f"    Label: {label}")

            self.stdout.write("")  # Blank line between groups

    def _invalidate_cache(self, group_name: str | None):
        """Invalidate the cache for dynamic choices."""
        ChoiceRegistry.invalidate_cache(group_name)
        self.stdout.write(self.style.SUCCESS(f"  Invalidated cache for group '{group_name}'."))

    def _sync_defaults(self, group_names: list[str] | None, recreate_defaults: bool, recreate_all: bool):
        """Synchronize default choices from code definitions to the database."""
        try:
            ChoiceRegistry.sync_defaults(group_names, recreate_defaults=recreate_defaults, recreate_all=recreate_all)
            for group_name, group_members in ChoiceRegistry._defaults.items():
                if group_names and group_name not in group_names:
                    continue
                self.stdout.write(f"  Synchronized '{group_name}' ...", ending="")
                self.stdout.write(self.style.SUCCESS(f" ({len(group_members)} choices)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error syncing choices: {e}"))
            raise e
