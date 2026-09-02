class Calculator:
    def __init__(self, precision=2):
        self.precision = precision

    def add(self, a, b):
        return round(a + b, self.precision)

    def subtract(self, a, b):
        return round(a - b, self.precision)

    def multiply(self, a, b):
        return round(a * b, self.precision)

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return round(a / b, self.precision)

    def power(self, base, exponent):
        return round(base ** exponent, self.precision)

    def sqrt(self, n):
        if n < 0:
            raise ValueError("Cannot take square root of negative number")
        return round(n ** 0.5, self.precision)

    def mean(self, numbers):
        if not numbers:
            raise ValueError("List cannot be empty")
        return round(sum(numbers) / len(numbers), self.precision)

    def median(self, numbers):
        if not numbers:
            raise ValueError("List cannot be empty")
        sorted_nums = sorted(numbers)
        n = len(sorted_nums)
        if n % 2 == 0:
            return round((sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2, self.precision)
        return round(sorted_nums[n//2], self.precision)


def format_result(value, unit=""):
    if unit:
        return f"{value} {unit}"
    return str(value)


def parse_expression(expr):
    tokens = expr.split()
    if len(tokens) != 3:
        raise ValueError("Expression must have format: number operator number")
    a, op, b = tokens
    try:
        a = float(a)
        b = float(b)
    except ValueError:
        raise ValueError("Operands must be numbers")
    ops = {"+": lambda x, y: x + y, "-": lambda x, y: x - y,
           "*": lambda x, y: x * y, "/": lambda x, y: x / y}
    if op not in ops:
        raise ValueError(f"Unknown operator: {op}")
    return ops[op](a, b)
