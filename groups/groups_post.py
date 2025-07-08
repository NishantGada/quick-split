from flask import request, jsonify
import uuid

from config.dbconfig import get_connection
from helper_functions import auth_required
from . import groups_bp


@groups_bp.route("/groups", methods=["POST"])
@auth_required
def create_group():
    data = request.get_json()
    creator_user_id = request.user["user_id"]
    
    try:
        user_id = request.user["user_id"]
        print("user_id: ", user_id)
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Error fetching user: {e}"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        group_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO `groups` (group_id, group_name, created_by) VALUES (%s, %s, %s)",
            (group_id, data["group_name"], user_id),
        )
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Error creating group: {e}"
        }), 400
    
    # Add creator user as member to group
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id) VALUES (%s, %s)",
        (group_id, creator_user_id),
    )
    
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({"success": True, "message": "Group created successfully"}), 201
