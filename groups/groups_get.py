from flask import request, jsonify

from config.dbconfig import get_connection
from helper_functions import auth_required, return_400_error_response
from . import groups_bp


@groups_bp.route("/groups", methods=["GET"])
@auth_required
def get_all_groups():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT group_id, group_name, created_at FROM `groups`")
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
