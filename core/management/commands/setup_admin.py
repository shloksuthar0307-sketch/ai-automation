import os
import secrets
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates default admin superuser if it does not already exist'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@sitewright.ai')
        password = os.environ.get('ADMIN_PASSWORD')
        generated = False

        if not password:
            password = secrets.token_urlsafe(16)
            generated = True

        if not User.objects.filter(username=username).exists():
            dummy_user = User(username=username, email=email)
            try:
                validate_password(password, user=dummy_user)
            except ValidationError as e:
                raise CommandError(f"Password validation failed: {'; '.join(e.messages)}")

            User.objects.create_superuser(username=username, email=email, password=password)

            if generated:
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] Created superuser '{username}' with generated password: {password}"
                ))
                self.stdout.write(self.style.WARNING(
                    "IMPORTANT: Store this password securely; it will not be shown again."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(f"[OK] Created superuser '{username}'."))
        else:
            self.stdout.write(self.style.SUCCESS(f"[OK] Admin superuser '{username}' is ready"))
