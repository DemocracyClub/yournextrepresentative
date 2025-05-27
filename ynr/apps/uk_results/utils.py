def calculate_turnout_percentage(turnout, total_electorate):
    """
    Calculate turnout as a percentage, rounded to two decimal places, based on turnout and total electorate
    """
    percentage = (turnout / total_electorate) * 100
    return min(round(percentage, 2), 100)
