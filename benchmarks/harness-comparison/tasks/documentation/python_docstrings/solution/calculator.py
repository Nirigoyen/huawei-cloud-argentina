class Calculator:
    """A calculator with configurable decimal precision for arithmetic operations.

    Args:
        precision (int): Number of decimal places to round results to. Defaults to 2.
    """

    def __init__(self, precision=2):
        """Initialize the calculator with a given precision.

        Args:
            precision (int): Number of decimal places for rounding. Defaults to 2.
        """
        self.precision = precision

    def add(self, a, b):
        """Add two numbers and round to the configured precision.

        Args:
            a (float): The first operand.
            b (float): The second operand.

        Returns:
            float: The sum of a and b, rounded to precision.
        """
        return round(a + b, self.precision)

    def subtract(self, a, b):
        """Subtract b from a and round to the configured precision.

        Args:
            a (float): The minuend.
            b (float): The subtrahend.

        Returns:
            float: The difference of a and b, rounded to precision.
        """
        return round(a - b, self.precision)

    def multiply(self, a, b):
        """Multiply two numbers and round to the configured precision.

        Args:
            a (float): The first factor.
            b (float): The second factor.

        Returns:
            float: The product of a and b, rounded to precision.
        """
        return round(a * b, self.precision)

    def divide(self, a, b):
        """Divide a by b and round to the configured precision.

        Args:
            a (float): The dividend.
            b (float): The divisor.

        Returns:
            float: The quotient of a and b, rounded to precision.

        Raises:
            ValueError: If b is zero.
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return round(a / b, self.precision)

    def power(self, base, exponent):
        """Raise base to the power of exponent.

        Args:
            base (float): The base number.
            exponent (float): The exponent.

        Returns:
            float: base raised to exponent, rounded to precision.
        """
        return round(base ** exponent, self.precision)

    def sqrt(self, n):
        """Compute the square root of n.

        Args:
            n (float): The number to take the square root of.

        Returns:
            float: The square root of n, rounded to precision.

        Raises:
            ValueError: If n is negative.
        """
        if n < 0:
            raise ValueError("Cannot take square root of negative number")
        return round(n ** 0.5, self.precision)

    def mean(self, numbers):
        """Compute the arithmetic mean of a list of numbers.

        Args:
            numbers (list[float]): A list of numeric values.

        Returns:
            float: The mean of the numbers, rounded to precision.

        Raises:
            ValueError: If the list is empty.
        """
        if not numbers:
            raise ValueError("List cannot be empty")
        return round(sum(numbers) / len(numbers), self.precision)

    def median(self, numbers):
        """Compute the median of a list of numbers.

        Args:
            numbers (list[float]): A list of numeric values.

        Returns:
            float: The median of the numbers, rounded to precision.

        Raises:
            ValueError: If the list is empty.
        """
        if not numbers:
            raise ValueError("List cannot be empty")
        sorted_nums = sorted(numbers)
        n = len(sorted_nums)
        if n % 2 == 0:
            return round((sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2, self.precision)
        return round(sorted_nums[n//2], self.precision)


def format_result(value, unit=""):
    """Format a numeric result with an optional unit string.

    Args:
        value (float): The numeric value to format.
        unit (str): Optional unit label to append. Defaults to empty string.

    Returns:
        str: The formatted result string.
    """
    if unit:
        return f"{value} {unit}"
    return str(value)


def parse_expression(expr):
    """Parse and evaluate a simple arithmetic expression string.

    Args:
        expr (str): Expression in format "number operator number"
            where operator is one of +, -, *, /.

    Returns:
        float: The result of the arithmetic operation.

    Raises:
        ValueError: If the expression format is invalid, operands are not
            numbers, or the operator is unknown.
    """
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
