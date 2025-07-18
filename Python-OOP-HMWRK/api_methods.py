from flask import Flask, jsonify, request, abort
from math_functions import pow, fibonacci, factorial

app = Flask(__name__)

@app.route('/pow', methods=['GET'])
def pow_route():
    base = request.args.get('base', type=float)
    exponent = request.args.get('exponent', type=float)

    if base is None or exponent is None:
        abort(400, description="Base and exponent are required to perform power op")

    result = pow(base, exponent)

    return jsonify({
        'base': base,
        'exponent': exponent,
        'result': result
    })

@app.route('/fibonacci', methods=['GET'])
def fibonacci_route():
    n = request.args.get('n', type=int)

    if n is None:
        abort(400, description="n is required to calculate fibonacci sequence")

    result = fibonacci(n)

    return jsonify({
        'n': n,
        'result': result
    })

@app.route('/factorial', methods=['GET'])
def factorial_route():
    n = request.args.get('n', type=int)

    if n is None:
        abort(400, description="n is required for factorial calculation")

    try:
        result = factorial(n)
    except ValueError as e:
        abort(400, description=str(e))

    return jsonify({
        'n': n,
        'result': result
    })

if __name__ == "__main__":
    app.run(debug=True)