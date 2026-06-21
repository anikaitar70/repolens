"""Entry point."""

from services.orders import build_order_report, process_orders


def main() -> None:
    sample = [{"id": 1, "status": "pending", "priority": "high", "amount": 150, "customer": {"verified": True}, "items": [{"in_stock": True, "price": 10}], "shipping": {"country": "US"}, "payment": {"method": "card"}, "session_token": "abc123456"}]
    print(process_orders(sample, {}))
    print(build_order_report(sample))


if __name__ == "__main__":
    main()
