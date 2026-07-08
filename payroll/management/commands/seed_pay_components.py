from django.core.management.base import BaseCommand

from payroll.models import PayComponent


class Command(BaseCommand):
    help = "Seed default payroll components"


    def handle(self, *args, **kwargs):

        components = [

            # Earnings
            {
                "name": "Basic Salary",
                "code": "BASIC",
                "component_type": "EARNING",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": True,
            },

            {
                "name": "House Allowance",
                "code": "HOUSE",
                "component_type": "EARNING",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": True,
            },

            {
                "name": "Transport Allowance",
                "code": "TRANSPORT",
                "component_type": "EARNING",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": True,
            },

            {
                "name": "Medical Allowance",
                "code": "MEDICAL",
                "component_type": "EARNING",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": False,
            },

            {
                "name": "Meal Allowance",
                "code": "MEAL",
                "component_type": "EARNING",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": True,
            },

            {
                "name": "Bonus",
                "code": "BONUS",
                "component_type": "EARNING",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": True,
            },

            {
                "name": "Commission",
                "code": "COMMISSION",
                "component_type": "EARNING",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": True,
            },

            # Statutory Deductions

            {
                "name": "PAYE",
                "code": "PAYE",
                "component_type": "TAX",
                "calculation_type": "PERCENTAGE",
                "percentage_rate": 30,
                "default_amount": 0,
                "is_taxable": False,
            },

            {
                "name": "NSSF",
                "code": "NSSF",
                "component_type": "DEDUCTION",
                "calculation_type": "PERCENTAGE",
                "percentage_rate": 6,
                "default_amount": 0,
                "is_taxable": False,
            },

            {
                "name": "SHIF",
                "code": "SHIF",
                "component_type": "DEDUCTION",
                "calculation_type": "PERCENTAGE",
                "percentage_rate": 2.75,
                "default_amount": 0,
                "is_taxable": False,
            },

            {
                "name": "Housing Levy",
                "code": "HOUSING",
                "component_type": "DEDUCTION",
                "calculation_type": "PERCENTAGE",
                "percentage_rate": 1.5,
                "default_amount": 0,
                "is_taxable": False,
            },

            # Custom

            {
                "name": "Loan Deduction",
                "code": "LOAN",
                "component_type": "DEDUCTION",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": False,
            },

            {
                "name": "Salary Advance",
                "code": "ADVANCE",
                "component_type": "DEDUCTION",
                "calculation_type": "FIXED",
                "default_amount": 0,
                "is_taxable": False,
            },

            {
                "name": "Pension",
                "code": "PENSION",
                "component_type": "DEDUCTION",
                "calculation_type": "PERCENTAGE",
                "percentage_rate": 5,
                "default_amount": 0,
                "is_taxable": False,
            },

        ]

        for component in components:

            PayComponent.objects.get_or_create(
                code=component["code"],
                defaults=component,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Payroll components seeded successfully."
            )
        )