from decimal import Decimal

from payroll.models import TaxBand


def calculate_paye(taxable_income, effective_date=None):
    paye = Decimal("0.00")

    tax_bands = TaxBand.objects.filter(
        name="PAYE",
        is_active=True,
    )

    if effective_date:
        latest_effective_date = (
            tax_bands
            .filter(effective_from__lte=effective_date)
            .order_by("-effective_from")
            .values_list("effective_from", flat=True)
            .first()
        )

        if latest_effective_date:
            tax_bands = tax_bands.filter(
                effective_from=latest_effective_date
            )
        else:
            tax_bands = tax_bands.none()

    tax_bands = tax_bands.order_by("min_income")

    for band in tax_bands:
        min_income = band.min_income
        max_income = band.max_income
        rate = band.rate / Decimal("100.00")

        if taxable_income <= min_income:
            continue

        upper_limit = (
            max_income
            if max_income is not None
            else taxable_income
        )

        taxable_amount = (
            min(taxable_income, upper_limit) - min_income
        )

        if taxable_amount > 0:
            paye += taxable_amount * rate

    return paye.quantize(Decimal("0.01"))
