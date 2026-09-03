from abc import ABC, abstractmethod
import re
from datetime import datetime


class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass


class CreditCardPayment(PaymentStrategy):
    def __init__(self, name, card_number, cvv, expiry_date):
        if not re.match(r"^\d{16}$", card_number):
            raise ValueError("Card number must be 16 digits")
        if not re.match(r"^\d{3}$", cvv):
            raise ValueError("CVV must be 3 digits")
        if not re.match(r"^\d{2}/\d{2}$", expiry_date):
            raise ValueError("Expiry must be MM/YY format")
        month, year = map(int, expiry_date.split("/"))
        if month < 1 or month > 12:
            raise ValueError("Invalid month")
        full_year = 2000 + year
        now = datetime.now()
        if full_year < now.year or (full_year == now.year and month < now.month):
            raise ValueError("Card expired")
        self.name = name
        self.card_number = card_number
        self.cvv = cvv
        self.expiry_date = expiry_date

    def pay(self, amount: float) -> bool:
        return True


class PayPalPayment(PaymentStrategy):
    def __init__(self, email, password):
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            raise ValueError("Invalid email format")
        self.email = email
        self.password = password

    def pay(self, amount: float) -> bool:
        return True


class CryptoPayment(PaymentStrategy):
    VALID_CRYPTOS = {"BTC", "ETH", "USDT"}

    def __init__(self, wallet_address, crypto_type):
        if not wallet_address.startswith("0x") or len(wallet_address) < 40:
            raise ValueError("Invalid wallet address")
        if crypto_type not in self.VALID_CRYPTOS:
            raise ValueError(f"Unsupported crypto type: {crypto_type}")
        self.wallet_address = wallet_address
        self.crypto_type = crypto_type

    def pay(self, amount: float) -> bool:
        return True


class PaymentContext:
    def __init__(self, strategy: PaymentStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: PaymentStrategy):
        self._strategy = strategy

    def process_payment(self, amount: float) -> bool:
        return self._strategy.pay(amount)


class PaymentProcessor:
    def __init__(self):
        self._strategies = {}

    def register_strategy(self, name, strategy: PaymentStrategy):
        self._strategies[name] = strategy

    def pay(self, name, amount: float) -> bool:
        return self._strategies[name].pay(amount)
