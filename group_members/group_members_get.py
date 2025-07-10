from flask import request, jsonify

from config.dbconfig import get_connection
from helper_functions import (
    auth_required,
    return_400_error_response,
    return_404_not_found,
)
from . import group_members_bp


def get_group_members_helper(user_id, group_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    print("checking if group exists")
    cursor.execute("SELECT group_name FROM `groups` WHERE group_id = %s", (group_id,))
    group = cursor.fetchone()
    if not group:
        return None, "Group not found"

    print("fetching all members")
    cursor.execute("SELECT user_id FROM group_members WHERE group_id = %s", (group_id,))
    members = cursor.fetchall()

    # Check if user is part of the group
    member_ids = [member["user_id"] for member in members]
    if user_id not in member_ids:
        return None, "User is not a member of this group"

    # Build a flat list of {name, id} dicts
    flat_members = []
    for member in members:
        cursor.execute(
            "SELECT first_name FROM users WHERE user_id = %s", (member["user_id"],)
        )
        user = cursor.fetchone()
        flat_members.append({
            "id": member["user_id"],
            "name": user["first_name"] if user else None
        })

    cursor.close()
    connection.close()

    return flat_members, None



@group_members_bp.route("/group/members/<string:group_id>", methods=["GET"])
@auth_required
def get_group_members(group_id):
    user_id = request.user["user_id"]

    members, error = get_group_members_helper(user_id, group_id)

    if error:
        return return_404_not_found(error)

    print("returning success response")
    return (
        jsonify(
            {
                "success": True,
                "message": "All group members fetched successfully",
                "data": {"members": members},
            }
        ),
        200,
    )
