import logging
from collections.abc import Iterable
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
from django.utils.text import slugify

from dbchoices.utils import generate_cache_key, get_choice_model

logger = logging.getLogger(__name__)
cache_timeout = getattr(settings, "DBCHOICES_CACHE_TIMEOUT", 1 * 60 * 60)  # Default: 1 hour

ChoiceModel = get_choice_model()


class ChoiceRegistry:
    """
    A registry for managing dynamic database-backed choices.

    This class provides generic methods to register, retrieve, and synchronize
    choices with the database.
    """

    _defaults: dict[str, Iterable[tuple[str, str]]] = {}
    _enum_cache: dict[str, type[models.TextChoices]] = {}

    @classmethod
    def register_defaults(cls, group_name: str, choices: Iterable[tuple[str | int, str | int]]) -> None:
        """Register default choices for a given `group_name`.

        Args:
            group_name (str):
                The name of the choice group. This should be unique to avoid potential conflicts.
            choices (Iterable[tuple[str, str]]):
                A list of tuples representing the choices in the format (value, label).
        """
        values_set = set()
        normalized_choices = []
        for item in choices:
            val, label = item[0], item[1]
            # Basic sanity checks to ensure value and label are valid
            if not isinstance(val, str | int):
                raise ValueError(f"Choice value must be a string or int, got {type(val).__name__} for {item}")
            if not isinstance(label, str | int):
                raise ValueError(f"Choice label must be a string or int, got {type(label).__name__} for {item}")
            if val in values_set:
                raise ValueError(f"Duplicate choice value '{val}' found in group '{group_name}'")

            values_set.add(str(val))
            normalized_choices.append((str(val), str(label)))

        cls._defaults[group_name] = normalized_choices

    @classmethod
    def get_choices(cls, group_name: str, **group_filters: Any) -> list[tuple[str, str]]:
        """Return a list of (value, label) for a given `group_name`.

        Args:
            group_name (str):
                The name of the choice group to retrieve choices for.
            **group_filters:
                Query filters to narrow down the choices. Useful in scenarios
                where choices may depend on other attributes.
        """
        cache_key = generate_cache_key(group_name, **group_filters)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        choice_queryset = ChoiceModel.get_choices(group_name, **group_filters)
        choices = list(choice_queryset.values_list("value", "label"))
        cache.set(cache_key, choices, timeout=cache_timeout)
        return choices

    @classmethod
    def get_label(cls, group_name: str, value: str, **group_filters: Any) -> str:
        """Translates a stored value to its label for a given group_name."""
        for db_val, label in cls.get_choices(group_name, **group_filters):
            if str(db_val) == value:
                return label
        return None

    @classmethod
    def get_enum(cls, group_name: str, **group_filters: Any) -> type[models.TextChoices]:
        """
        Generates a dynamic `TextChoices` enum for the given group_name.

        Args:
            group_name (str):
                The name of the choice group to retrieve choices for.
            **group_filters:
                Query filters to narrow down the choices. Useful in scenarios
                where choices may depend on other attributes.
        """
        cache_key = generate_cache_key(group_name, **group_filters)
        if cache_key not in cls._enum_cache:
            members = {}
            choices = cls.get_choices(group_name, **group_filters)
            for val, label in choices:
                # Create valid python identifier: 'In Progress' -> 'IN_PROGRESS'
                safe_key = slugify(str(val)).replace("-", "_").upper()
                if not safe_key or safe_key[0].isdigit():
                    safe_key = f"K_{safe_key}"

                members[safe_key] = (val, label)

            # Dynamically create a TextChoices subclass
            class_name = f"{group_name.title().replace('_', '')}Choices"
            cls._enum_cache[cache_key] = models.TextChoices(class_name, members)

        return cls._enum_cache[cache_key]

    @classmethod
    def sync_defaults(
        cls, group_names: list[str] | None = None, recreate_defaults: bool = True, recreate_all: bool = False
    ) -> None:
        """Recreate all default choices from code definitions.

        Args:
            group_names (list[str] | None):
                A list of group names to sync. If None, all registered groups will be synced.
            recreate_defaults (bool):
                If True, all choices that are no longer a part of the default definitions will be deleted.
            recreate_all (bool):
                If True, the entire set of default choices will be deleted and recreated. It can potentially
                delete user-added choices as well. Use with caution.
        """
        # Accumulate all default choice instances to be created/updated
        choice_instances = [
            ChoiceModel(
                group_name=group,
                value=value,
                label=label,
                ordering=idx,
                is_system_default=True,
            )
            for group, items in cls._defaults.items()
            for idx, (value, label) in enumerate(items)
            if group_names is None or group in group_names
        ]
        if not choice_instances:
            logger.info("No default choices to synchronize.")
            return

        with transaction.atomic():
            if recreate_all:
                logger.info("Recreating all default choices.")
                ChoiceModel._delete_choices(list(cls._defaults.keys()))
            elif recreate_defaults:
                logger.info("Deleting abandoned default choices.")
                ChoiceModel._delete_choices(list(cls._defaults.keys()), is_system_default=True)

            ChoiceModel._create_choices(choice_instances)
            logger.info(f"Synchronized {len(cls._defaults)} groups and {len(choice_instances)} choices.")

        for group_name in cls._defaults:
            cls.invalidate_cache(group_name)

    @classmethod
    def invalidate_cache(cls, group_name: str, **group_filters: Any) -> None:
        """Invalidate dynamic choice cache from the application."""
        # Note: This only invalidates the cache for the specific group_name and group_filters.
        # Invalidating all caches would require tracking all keys, or using a different caching strategy.
        cache_key = generate_cache_key(group_name, **group_filters)
        cache.delete(cache_key)

        if cache_key in cls._enum_cache:
            del cls._enum_cache[cache_key]
