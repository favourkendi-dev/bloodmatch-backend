import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Creates or updates a superuser with role='admin' from env vars"

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv('ADMIN_USERNAME')
        email = os.getenv('ADMIN_EMAIL', '')
        password = os.getenv('ADMIN_PASSWORD')

        if not username or not password:
            self.stdout.write("ADMIN_USERNAME/ADMIN_PASSWORD not set, skipping.")
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True, 'role': 'admin'},
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"Superuser '{username}' created with role='admin'.")
        else:
            changed = False
            if user.role != 'admin':
                user.role = 'admin'
                changed = True
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                changed = True
            if changed:
                user.save()
                self.stdout.write(f"Updated existing user '{username}' to admin role/permissions.")
            else:
                self.stdout.write(f"Superuser '{username}' already exists with correct role, skipping.")
