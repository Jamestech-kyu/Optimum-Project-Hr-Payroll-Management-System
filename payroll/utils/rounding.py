from decimal import Decimal


def round_money(value):
    return Decimal(value).quantize(Decimal("0.01"))
