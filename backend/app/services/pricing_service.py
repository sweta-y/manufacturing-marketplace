from decimal import Decimal, InvalidOperation, ROUND_DOWN

CENT = Decimal("0.01")


def parse_price(value):
    if value is None:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return amount if amount.is_finite() else None


def manufacturer_price_limit(customer_price):
    price = parse_price(customer_price)
    if price is None or price < 0:
        return None
    return (price * Decimal("0.75")).quantize(CENT, rounding=ROUND_DOWN)


def valid_manufacturer_quote(customer_price, manufacturer_price):
    customer = parse_price(customer_price)
    quote = parse_price(manufacturer_price)
    limit = manufacturer_price_limit(customer)
    if customer is None or customer < 0 or quote is None or quote < 0 or limit is None:
        return False
    try:
        has_cent_precision = quote == quote.quantize(CENT)
    except InvalidOperation:
        return False
    return has_cent_precision and quote <= limit


def calculate_admin_profit(customer_price, manufacturer_price):
    customer = parse_price(customer_price)
    manufacturer = parse_price(manufacturer_price)
    if customer is None or manufacturer is None:
        return None
    return customer - manufacturer
