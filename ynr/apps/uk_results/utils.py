from decimal import ROUND_HALF_UP, Decimal


def calculate_turnout_percentage(turnout, total_electorate):
    """
    Calculate turnout as a percentage, rounded to two decimal places, based on turnout and total electorate
    """
    if total_electorate == 0:
        return Decimal("0.00")

    turnout = Decimal(turnout)
    total_electorate = Decimal(total_electorate)

    percentage = (turnout / total_electorate) * Decimal("100")
    percentage = percentage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return min(percentage, Decimal("100.00"))
