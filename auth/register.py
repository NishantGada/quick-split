from flask import request, jsonify
import uuid

from config.dbconfig import get_connection
from auth.helper_functions import is_duplicate_email
from . import auth_bp

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    connection = get_connection()
    cursor = connection.cursor()
    
    if is_duplicate_email(data.get("email")):
        return (
            jsonify({"success": False, "message": "Email already registered"}),
            400,
        )
    
    try:
        user_id = str(uuid.uuid4())
        query = """INSERT INTO users (user_id, first_name, last_name, email, password, dob) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                user_id,
                data.get("first_name"),
                data.get("last_name"),
                data.get("email"),
                data.get("password"),
                data.get("dob"),
            ),
        )

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"success": True, "message": "User created successfully"}), 201
    except Exception as e:
        return (
            jsonify({"success": False, "message": e}),
            500,
        )
