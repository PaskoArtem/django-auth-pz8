
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create an administrator using environment variables"

    def handle(self, *args, **options):
        username = os.environ.get("DEPLOY_ADMIN_USERNAME")
        password = os.environ.get("DEPLOY_ADMIN_PASSWORD")

        if not username or not password:
            raise CommandError(
                "DEPLOY_ADMIN_USERNAME and DEPLOY_ADMIN_PASSWORD must be set."
            )

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)

        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS("Administrator created."))
        else:
            self.stdout.write(
                self.style.SUCCESS("Administrator password updated.")
            )
