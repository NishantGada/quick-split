from flask import request, jsonify

from config.dbconfig import get_connection
from helper_functions import (
    auth_required,
    return_400_error_response,
    return_404_not_found,
)
from . import group_members_bp


@group_members_bp.route(
    "/group/<string:group_id>/members/<string:user_id>", methods=["DELETE"]
)
@auth_required
def remove_member_from_group(group_id, user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # basic auth user
    auth_user = request.user["user_id"]

    print("checking if group exists")
    cursor.execute("SELECT group_name FROM `groups` WHERE group_id = %s", (group_id,))
    group = cursor.fetchone()
    if not group:
        return return_404_not_found("Group not found")

    print("fetching all members")
    cursor.execute("SELECT user_id FROM group_members WHERE group_id = %s", (group_id,))
    members = cursor.fetchall()
    print("members: ", members)

    if auth_user not in [member["user_id"] for member in members]:
        return return_404_not_found("Invalid Group ID")

    if user_id not in [member["user_id"] for member in members]:
        return return_404_not_found("User already not in Group")

    print("removing user: ", user_id)
    try:
        cursor.execute(
            "DELETE FROM group_members WHERE group_id = %s AND user_id=%s",
            (group_id, user_id),
        )
    except Exception as e:
        return return_400_error_response(e)

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"success": True, "message": "User deleted successfully"}), 204
