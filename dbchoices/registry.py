from typing import Any

from dbchoices.utils import get_choice_model

ChoiceModel = get_choice_model()


class ChoiceRegistry:
    @classmethod
    def get_choices(cls, group_name: str, **filters: Any) -> list[tuple[str, str]]:
        """Returns list of (value, label) for a given `group_name`.

        Optionally, `filters` can be passed to narrow down choices.
        Useful in scenarios where choices may depend on other attributes.
        """
