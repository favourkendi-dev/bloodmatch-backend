import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Creates a superuser from env vars if one doesn't already exist"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv('ADMIN_USERNAME')
        email = os.getenv('ADMIN_EMAIL', '')
        password = os.getenv('ADMIN_PASSWORD')

        if not username or not password:
            self.stdout.write("ADMIN_USERNAME/ADMIN_PASSWORD not set, skipping.")
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' already exists, skipping.")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(f"Superuser '{username}' created.")
