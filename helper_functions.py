from flask import jsonify, request
from functools import wraps

from config.dbconfig import get_connection


def validate_request(*args):
    if not all([args]):
        print("Request body error!")
        return False
    return True


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return (
                jsonify({"error": "Authorization required"}),
                401,
                {"WWW-Authenticate": 'Basic realm="Login Required"'},
            )

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (auth.username,))
        user = cursor.fetchone()

        if not user or user["password"] != auth.password:
            return jsonify({"error": "Invalid credentials"}), 401

        # optionally attach user info to the request context
        request.user = user
        return f(*args, **kwargs)

    return decorated


def return_400_error_response(e):
    return jsonify({"success": False, "message": f"An error occurred: {e}"}), 400


def return_404_not_found(e):
    return jsonify({"success": False, "message": f"An error occurred: {e}"}), 404


def return_200_response(message, data):
    return (
        jsonify(
            {
                "success": True,
                "message": message,
                "data": data,
            }
        ),
        200,
    )
