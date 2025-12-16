# django-dbchoices

## ⚡ Simple Runtime Choices for Django Models & Forms

**`django-dbchoices`** provides a clean, lightweight way to manage dynamic choices in Django; backed by the database. It’s built for cases where valid choices depend on context—such as tenancy, environment, or configuration—and where hard-coded enums or frequent migrations become a bottleneck.

### Key Features

* **Plug-and-play integration:** Works seamlessly with Django Models, Forms, Admin, DRF, and more.
* **Runtime Evaluation:** Choices are resolved dynamically when models and forms are loaded.
* **Code-defined defaults:** Declare default choices in code and easily sync them to the database.
* **Built-in caching:** Reduces database hits and keeps performance snappy.
* **Swappable by design:** Bring your own model to support multi-tenancy or attach extra metadata.

-----

## 📦 Installation & Setup

```bash
pip install django-dbchoices
```

Add to your `settings.py`:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'dbchoices',
]
```

### Workflow

1.  **Migrate:** Apply the package's initial migrations.

    ```bash
    python manage.py migrate
    ```

2.  **Define Defaults:** Register your required choices in your application's `AppConfig.ready()` method:

    ```python
    class MyAppConfig(AppConfig):
        name = 'myapp'

        def ready(self) -> None:
            from dbchoices.registry import ChoiceRegistry

            # Register choices using tuples
            ChoiceRegistry.register_defaults("Status", [
                ("PENDING", "Booking Pending"),
                ("COMPLETE", "Booking Complete"),
                ("FAILED", "Booking Failed"),
            ])

            # Or using TextChoices and/or Enums
            ChoiceRegistry.register_enum(StatusEnum)
    ```

3.  **Synchronize:** Run the management command to push your code definitions into the database.

    ```bash
    python manage.py dbchoices --sync
    ```

And you're all set! Your choices are now ready for use in models and forms.

-----

## Usage

### Defining Models

Use the custom `DynamicChoiceField` to define the choice field(s) in the models. This field handles the necessary hooks
for validation and display.

```python
# myapp/models.py
from dbchoices.fields import DynamicChoiceField

class Ticket(models.Model):
    status = DynamicChoiceField(group_key='Status', default='PENDING')
```

Alternatively, if you wish to keep using standard Django fields, you can use [DynamicChoiceValidator](dbchoices/validators.py).

_Note: This approach does not support automatic label/choice rendering in Django Admin/Forms._

```python
# myapp/models.py
from django.db import models
from dbchoices.registry import ChoiceRegistry

class Ticket(models.Model):
    status = models.CharField(
        default='PENDING',
        validators=[DynamicChoiceValidator(group_key='Status')],
    )
```

### API Access

The registry also provides helper methods for obtaining human-readable labels and `models.TextChoices` in your code logic.

_Note: It is discouraged to use `get_enum` in typing-critical paths due to the ephemeral nature of runtime choices._

```python
from dbchoices.registry import ChoiceRegistry

# Get the readable label
readable_status = ChoiceRegistry.get_label('ticket_status', 'in_progress')

# Get the Enum class for code logic
Status = ChoiceRegistry.get_enum('ticket_status')
if ticket.status == Status.CLOSED:
    # ...
```

-----

## Settings
You can customize the behavior of `django-dbchoices` using the following settings in your `settings.py`:
```python
# settings.py
# Cache timeout for dynamic choices (default: 1 hour)
DBCHOICES_CACHE_TIMEOUT = 3600

# Cache alias to use for caching dynamic choices (default: 'default')
DBCHOICES_CACHE_ALIAS = 'default'

# Whether to auto-invalidate cache on choice updates (default: True)
DBCHOICES_AUTO_INVALIDATE_CACHE = True

# Custom choice model path (default: 'dbchoices.Choice')
DBCHOICE_MODEL = 'myapp.CustomChoiceModel'
```

-----

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
