from django.conf import settings
from django.core.management import BaseCommand
from django.utils import autoreload


class BaseAutoReloadCommand(BaseCommand):
    """
    Django-command base class with auto-reload.

    It is recommended to use it when implementing long-running workers ONLY IN DEVELOPMENT.
    The command uses the auto-reload mechanism from django and will reload the process if
    django-reloader detects changes in the code.

    The class retains the functionality of BaseCommand,
    only replaces `handle` method with 'run_command'.
    """

    def handle(self, *args, **kwargs):
        if settings.DEBUG:
            autoreload.run_with_reloader(self.run_command, *args, **kwargs)
        else:
            self.run_command(*args, **kwargs)

    def run_command(self, *args, **kwargs):
        raise NotImplementedError('Method `run_command not implemented.`')
