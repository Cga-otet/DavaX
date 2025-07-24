from flask import Flask, jsonify, request, abort
from math_functions import pow, fibonacci, factorial
import sqlite3

app = Flask(__name__)

DB_PATH = 'api_log.db'

def init_db():
    """Initialize the DB and create the log table if it doesn't exist."""
    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        conn.execute('''
          CREATE TABLE IF NOT EXISTS api_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                parameters TEXT NOT NULL
              );
              '''
        )

def log_usage(method, **kwargs):
    """ 
    Insert a row into usage log. 
    Methods are pow, fibonacci or factorial.
    kwargs can include base, exponent or n as appropiate
    """
    parameters_str = ','.join(f"{key}={value}" for key, value in kwargs.items())
    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        conn.execute(
          "INSERT INTO api_log (method, parameters) VALUES (?, ?)",
          (method, parameters_str)
        )


@app.route('/pow', methods=['GET'])
def pow_route():
    base = request.args.get('base', type=float)
    exponent = request.args.get('exponent', type=float)

    if base is None or exponent is None:
        abort(400, description="Base and exponent are required to perform power op")

    result = pow(base, exponent)

    log_usage("pow", base=base, exponent=exponent)

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

    log_usage("fibonacci", n=n)

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

    log_usage("factorial", n=n)

    return jsonify({
        'n': n,
        'result': result
    })

@app.route('/log', methods=['GET'])
def logs():
    """Retrieve database logs of API usage"""
    limit =  request.args.get('limit', default=50, type=int)

    with sqlite3.connect(DB_PATH, timeout=5) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql_string = 'SELECT * FROM api_log ORDER BY timestamp DESC '
        if limit:
            sql_string += 'LIMIT ?'
            cursor.execute(sql_string, (limit,))
        else:
            cursor.execute(sql_string)
        rows = [dict(r) for r in cursor.fetchall()]
    return jsonify(rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)