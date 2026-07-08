from django.core.management.base import BaseCommand
from datetime import date
from payroll.models import TaxBand, StatutoryRate, Currency, PayrollPolicy


class Command(BaseCommand):
    help = "Seed payroll configuration data"

    def handle(self, *args, **kwargs):
        kes, _ = Currency.objects.get_or_create(
            code="KES",
            defaults={
                "name": "Kenyan Shilling",
                "symbol": "KSh",
                "is_base_currency": True,
            },
        )

        currencies = [
            ("USD", "US Dollar", "$"),
            ("EUR", "Euro", "€"),
            ("GBP", "British Pound", "£"),
            ("UGX", "Ugandan Shilling", "USh"),
            ("TZS", "Tanzanian Shilling", "TSh"),
        ]

        for code, name, symbol in currencies:
            Currency.objects.get_or_create(
                code=code,
                defaults={"name": name, "symbol": symbol},
            )

        tax_bands = [
            (0, 24000, 10),
            (24001, 32333, 25),
            (32334, None, 30),
        ]

        for min_income, max_income, rate in tax_bands:
            TaxBand.objects.get_or_create(
                name="PAYE",
                min_income=min_income,
                max_income=max_income,
                effective_from=date(2026, 1, 1),
                defaults={"rate": rate},
            )

        statutory_rates = [
            ("NSSF", "NSSF", "NSSF", 6),
            ("SHIF", "SHIF", "SHIF", 2.75),
            ("Housing Levy", "HOUSING_LEVY", "HOUSING_LEVY", 1.5),
        ]

        for name, code, statutory_type, rate in statutory_rates:
            StatutoryRate.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "statutory_type": statutory_type,
                    "rate": rate,
                    "is_percentage": True,
                    "effective_from": date(2026, 1, 1),
                },
            )

        PayrollPolicy.objects.get_or_create(
            name="Default Payroll Policy",
            defaults={
                "working_days_per_month": 22,
                "working_hours_per_day": 8,
                "overtime_multiplier": 1.5,
                "weekend_overtime_multiplier": 2,
                "payroll_cutoff_day": 25,
                "payslip_generation_day": 28,
                "currency": kes,
            },
        )

        self.stdout.write(
            self.style.SUCCESS("Payroll configuration seeded successfully.")
        )