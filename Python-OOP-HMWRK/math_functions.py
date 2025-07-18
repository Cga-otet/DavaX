def pow(base, exponent):
    """Calculate base raised to the power of exponent."""

    return base ** exponent

def fibonacci(n):
    """Return the n-th Fibonacci number."""
    
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def factorial(n):
    """Calculate the factorial of a number."""

    if n < 0 :
        raise ValueError("Factorial not defined for negative numbers")
    elif n == 0 or n == 1:
        return 1
    else:
        result = 1
        for i in range (2, n + 1):
            result = result * i
        return result

