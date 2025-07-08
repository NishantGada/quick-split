from flask import request, jsonify

from config.dbconfig import get_connection
from helper_functions import auth_required, return_400_error_response, return_404_not_found
from . import group_members_bp

@group_members_bp.route("/group/members/<string:group_id>", methods=["GET"])
@auth_required
def get_group_members(group_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    user_id = request.user["user_id"]

    print("checking if group exists")
    cursor.execute("SELECT group_name FROM `groups` WHERE group_id = %s", (group_id,))
    group = cursor.fetchone()
    if not group:
        return return_404_not_found("Group not found")
    

    print("fetching all members")
    cursor.execute("SELECT user_id FROM group_members WHERE group_id = %s", (group_id,))
    members = cursor.fetchall()
    print("members: ", members)
    if user_id not in [member['user_id'] for member in members]:
        return return_404_not_found("Invalid Group ID")

    member_ids = [member['user_id'] for member in members]

    print("returning success response")
    return jsonify({
        "success": True, 
        "message": "All group members fetched successfully", 
        "data": {
            "members": member_ids
        }
    }), 200
