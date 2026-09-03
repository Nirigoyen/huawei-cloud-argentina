import pytest
from solution import (
    PaymentStrategy, CreditCardPayment, PayPalPayment,
    CryptoPayment, PaymentContext, PaymentProcessor,
)


class TestCreditCardPayment:
    def test_valid_credit_card(self):
        payment = CreditCardPayment("John Doe", "1234567890123456", "123", "12/28")
        assert payment.pay(100.0) is True

    def test_invalid_card_number_short(self):
        with pytest.raises(ValueError):
            CreditCardPayment("John", "123", "123", "12/28")

    def test_invalid_card_number_non_digit(self):
        with pytest.raises(ValueError):
            CreditCardPayment("John", "123456789012345a", "123", "12/28")

    def test_invalid_cvv(self):
        with pytest.raises(ValueError):
            CreditCardPayment("John", "1234567890123456", "12", "12/28")

    def test_invalid_cvv_non_digit(self):
        with pytest.raises(ValueError):
            CreditCardPayment("John", "1234567890123456", "abc", "12/28")

    def test_expired_card(self):
        with pytest.raises(ValueError):
            CreditCardPayment("John", "1234567890123456", "123", "12/20")

    def test_invalid_expiry_format(self):
        with pytest.raises(ValueError):
            CreditCardPayment("John", "1234567890123456", "123", "1228")


class TestPayPalPayment:
    def test_valid_paypal(self):
        payment = PayPalPayment("user@example.com", "password123")
        assert payment.pay(50.0) is True

    def test_invalid_email(self):
        with pytest.raises(ValueError):
            PayPalPayment("not-an-email", "password123")

    def test_invalid_email_no_domain(self):
        with pytest.raises(ValueError):
            PayPalPayment("user@", "password123")


class TestCryptoPayment:
    def test_valid_crypto_eth(self):
        addr = "0x" + "a" * 40
        payment = CryptoPayment(addr, "ETH")
        assert payment.pay(1.0) is True

    def test_valid_crypto_btc(self):
        addr = "0x" + "b" * 40
        payment = CryptoPayment(addr, "BTC")
        assert payment.pay(1.0) is True

    def test_invalid_wallet_address(self):
        with pytest.raises(ValueError):
            CryptoPayment("short", "ETH")

    def test_invalid_wallet_no_prefix(self):
        with pytest.raises(ValueError):
            CryptoPayment("a" * 42, "ETH")

    def test_invalid_crypto_type(self):
        addr = "0x" + "a" * 40
        with pytest.raises(ValueError):
            CryptoPayment(addr, "DOGE")


class TestPaymentContext:
    def test_context_delegates(self):
        strategy = PayPalPayment("user@example.com", "pass")
        ctx = PaymentContext(strategy)
        assert ctx.process_payment(100.0) is True

    def test_context_set_strategy(self):
        ctx = PaymentContext(PayPalPayment("user@example.com", "pass"))
        ctx.set_strategy(CreditCardPayment("John", "1234567890123456", "123", "12/28"))
        assert ctx.process_payment(200.0) is True


class TestPaymentProcessor:
    def test_register_and_pay(self):
        processor = PaymentProcessor()
        processor.register_strategy("paypal", PayPalPayment("user@example.com", "pass"))
        processor.register_strategy("card", CreditCardPayment("John", "1234567890123456", "123", "12/28"))
        assert processor.pay("paypal", 50.0) is True
        assert processor.pay("card", 100.0) is True

    def test_unknown_strategy(self):
        processor = PaymentProcessor()
        with pytest.raises(KeyError):
            processor.pay("unknown", 100.0)


class TestAbstractBase:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            PaymentStrategy()
