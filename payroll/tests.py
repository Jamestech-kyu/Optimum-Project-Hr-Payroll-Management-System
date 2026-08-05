from django.test import TestCase

# Create your tests here.
from datetime import date
from decimal import Decimal

from django.test import TestCase

from .models import StatutoryRate, TaxBand
from .services import calculate_paye, calculate_statutory_deductions


class PayrollComplianceCalculationTests(TestCase):
    def test_paye_uses_bands_effective_for_the_payroll_period(self):
        TaxBand.objects.create(
            name="PAYE",
            min_income=Decimal("0.00"),
            max_income=Decimal("1000.00"),
            rate=Decimal("10.00"),
            effective_from=date(2026, 1, 1),
        )
        TaxBand.objects.create(
            name="PAYE",
            min_income=Decimal("0.00"),
            max_income=Decimal("1000.00"),
            rate=Decimal("20.00"),
            effective_from=date(2026, 8, 1),
        )

        self.assertEqual(
            calculate_paye(Decimal("1000.00"), date(2026, 7, 31)),
            Decimal("100.00"),
        )
        self.assertEqual(
            calculate_paye(Decimal("1000.00"), date(2026, 8, 31)),
            Decimal("300.00"),
        )

    def test_statutory_rates_are_not_applied_before_their_effective_date(self):
        StatutoryRate.objects.create(
            name="SHIF",
            code="SHIF-2026",
            statutory_type="SHIF",
            rate=Decimal("2.75"),
            effective_from=date(2026, 8, 1),
        )

        self.assertEqual(
            calculate_statutory_deductions(
                Decimal("1000.00"), date(2026, 7, 31)
            ),
            {},
        )
        self.assertEqual(
            calculate_statutory_deductions(
                Decimal("1000.00"), date(2026, 8, 31)
            ),
            {"SHIF": Decimal("27.50")},
        )
