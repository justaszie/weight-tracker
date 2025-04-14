def to_signed_amt_str(amount, decimals=True):
    return ('+' if amount >= 0 else '-') + (f'{abs(amount):.2f}' if decimals else str(abs(amount)))
