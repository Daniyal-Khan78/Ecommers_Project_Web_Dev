from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        """
        ready() is called once when Django finishes loading all apps.
        We import signals here so Django registers them at startup.

        If we imported signals at the top of models.py or views.py,
        they might not be registered at the right time. The ready()
        method in AppConfig is the officially recommended place.
        """
        import users.signals  # noqa: F401
