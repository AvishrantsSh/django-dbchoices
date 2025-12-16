import logging
from collections.abc import Iterable
from enum import Enum
from typing import Any

from django.conf import settings
from django.core.cache import caches
from django.db import models, transaction
from django.utils.regex_helper import _lazy_re_compile
from django.utils.text import slugify

from dbchoices.utils import generate_cache_key, get_choice_model

logger = logging.getLogger(__name__)
cache_timeout = getattr(settings, "DBCHOICES_CACHE_TIMEOUT", 1 * 60 * 60)  # Default: 1 hour
cache = caches[getattr(settings, "DBCHOICES_CACHE_ALIAS", "default")]
safe_slug_regex = _lazy_re_compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


ChoiceModel = get_choice_model()
EnumTuple = tuple[str, str, str]
"""A tuple representing an enum member with (name, value, label)."""


class ChoiceRegistry:
    """
    A registry for managing dynamic database-backed choices.

    This class provides generic methods to register, retrieve, and synchronize
    choices with the database.
    """

    _defaults: dict[str, Iterable[EnumTuple]] = {}
    _enum_cache: dict[str, type[models.TextChoices]] = {}

    @classmethod
    def register_defaults(cls, group_name: str, choices: Iterable[EnumTuple | tuple[str, str]]) -> None:
        """Register default choices for a given `group_name`.

        Args:
            group_name (str):
                The name of the choice group. This should be unique to avoid potential conflicts.
            choices (Iterable[EnumTuple | tuple[str, str]]):
                A list of tuples representing the choices to register.
        """

        def _sanitize_value(val) -> str:
            return str(val).strip()

        name_set = set()
        values_set = set()
        normalized_choices = []
        for item in choices:
            # Unpack the choice tuple and normalize to strings
            if not isinstance(item, tuple | list) or len(item) not in (2, 3):
                raise ValueError(
                    f"Invalid choice format '{item}' in group '{group_name}'. "
                    "Expected a tuple of (name, value) or (name, value, label)."
                )

            name_str = _sanitize_value(item[0])
            value_str = _sanitize_value(item[1])
            label_str = _sanitize_value(item[2]) if len(item) == 3 else value_str

            if value_str in values_set:
                raise ValueError(f"Duplicate choice value '{value_str}' found in group '{group_name}'")

            values_set.add(value_str)
            if safe_slug_regex.match(name_str) is None:
                name_str_slug = slugify(name_str).replace("-", "_").upper()
                logger.warning(
                    f"Choice '{name_str}' in group '{group_name}' is not a valid Python identifier."
                    f" The choice name will be slugified to '{name_str_slug}'."
                )
                name_str = name_str_slug

            if name_str in name_set:
                raise ValueError(f"Duplicate choice name '{name_str}' found in group '{group_name}'")

            name_set.add(name_str)
            normalized_choices.append((name_str, value_str, label_str))

        cls._defaults[group_name] = normalized_choices

    @classmethod
    def register_enum(cls, enum_cls: type[Enum | models.Choices], group_name: str | None = None) -> None:
        """Register choices from a given Enum class.

        Args:
            enum_cls (type[Enum | models.Choices]):
                The Enum class containing choice definitions.
            group_name (str | None):
                The name of the choice group. If None, the Enum class name will be used.
        """
        if not issubclass(enum_cls, Enum):
            raise ValueError("Provided class is not a subclass of Enum.")

        if group_name is None:
            group_name = enum_cls.__name__

        choices = []
        for member in enum_cls:
            if issubclass(enum_cls, models.Choices):
                choices.append((member.name, str(member.value), str(member.label)))
            elif isinstance(member.value, tuple):
                choices.append((member.name, str(member.value[0]), str(member.value[1])))
            else:
                choices.append((member.name, str(member.value), str(member.name)))

        cls._defaults[group_name] = choices

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
    def get_label(cls, group_name: str, value: str, default: Any = None, **group_filters: Any) -> str:
        """Translates a stored value to its label for a given group_name."""
        for db_val, label in cls.get_choices(group_name, **group_filters):
            if str(db_val) == value:
                return label
        return default

    @classmethod
    def get_enum(cls, group_name: str, **group_filters: Any) -> type[models.TextChoices]:
        """
        Generates a dynamic `TextChoices` enum for the given group_name. The enum members
        only include choices registered as system defaults.

        Args:
            group_name (str):
                The name of the choice group to retrieve choices for.
            **group_filters:
                Query filters to narrow down the choices. Useful in scenarios
                where choices may depend on other attributes.
        """
        group_filters["is_system_default"] = True  # Only include system default choices in enums
        cache_key = generate_cache_key(group_name, **group_filters)
        if cache_key not in cls._enum_cache:
            members = {}
            choices = cls.get_choices(group_name, **group_filters)
            if not choices:
                raise ValueError(f"No choices found for group '{group_name}' to create enum.")

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
        if group_names is None:
            group_names = list(cls._defaults.keys())

        choice_instances = [
            ChoiceModel(
                group_name=group,
                name=name,
                value=value,
                label=label,
                ordering=idx,
                is_system_default=True,
            )
            for group, items in cls._defaults.items()
            for idx, (name, value, label) in enumerate(items)
            if group in group_names
        ]
        if not choice_instances:
            logger.info("No default choices to synchronize.")
            return

        with transaction.atomic():
            if recreate_all:
                logger.info("Recreating all default choices.")
                ChoiceModel._delete_choices(group_names)
            elif recreate_defaults:
                logger.info("Deleting abandoned default choices.")
                ChoiceModel._delete_choices(group_names, is_system_default=True)

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
