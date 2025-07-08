from flask import request, jsonify

from config.dbconfig import get_connection
from helper_functions import auth_required, return_400_error_response
from . import users_bp

@users_bp.route("/users", methods=["GET"])
def get_all_users():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    return jsonify({
        "success": True, 
        "message": "All users fetched successfully", 
        "data": {
            "users": users
        }
    }), 200


@users_bp.route("/user/groups", methods=["GET"])
@auth_required
def get_user_groups():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    user_id = request.user["user_id"]

    try:
        cursor.execute("SELECT group_id, group_name, created_at FROM `groups` WHERE created_by = %s", (user_id,))
        groups = cursor.fetchall()
    except Exception as e:
        return return_400_error_response(e)

    return jsonify({
        "success": True, 
        "message": "All groups fetched successfully", 
        "data": {
            "groups": groups
        }
    }), 200