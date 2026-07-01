from django.core.management.base import BaseCommand
from accounts.models import Role


class Command(BaseCommand):
    help = "Seed default system roles"

    def handle(self, *args, **kwargs):
        roles = [
            ("SUPER_ADMIN", "Super Admin"),
            ("ADMIN", "Admin"),
            ("HR", "HR"),
            ("MANAGER", "Manager"),
            ("PAYROLL_OFFICER", "Payroll Officer"),
            ("EMPLOYEE", "Employee"),
        ]

        for role_name, description in roles:
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={"description": description}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created role: {description}"))
            else:
                self.stdout.write(self.style.WARNING(f"Role already exists: {description}"))