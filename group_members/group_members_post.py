from flask import request, jsonify

from config.dbconfig import get_connection
from helper_functions import auth_required, return_400_error_response, return_404_not_found
from . import group_members_bp


@group_members_bp.route("/group/members", methods=["POST"])
@auth_required
def add_member_to_group():
    data = request.get_json()
    print("data: ", data)
    group_creator_id = request.user["user_id"]

    connection = get_connection()
    cursor = connection.cursor()
    
    if data["group_name"] is None or data["user_id"] is None:
        return return_400_error_response("Missing required parameters")

    # Validate if group being added into is owned by basic auth user
    cursor.execute(
        "SELECT created_by FROM `groups` WHERE group_name = %s", (data["group_name"],)
    )
    created_by = cursor.fetchone()[0]
    if created_by != group_creator_id:
        return return_400_error_response("Invalid group name")
    

    # Get group_id by group_name
    cursor.execute("SELECT group_id FROM `groups` WHERE group_name = %s", (data["group_name"],))
    group_id = cursor.fetchone()[0]
    print("group_id: ", group_id)
    

    # Validate if basic auth user himself is in the group or not
    cursor.execute("SELECT user_id FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, group_creator_id))
    user = cursor.fetchone()
    print("user: ", user)
    if not user:
        return return_400_error_response("You cannot add someone to a group that you are not a part of")


    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (data["user_id"],))
    user = cursor.fetchone()
    print("user: ", user)
    if user is None:
        return return_404_not_found("User does not exist")


    # Check if user already exists in the group
    cursor.execute("SELECT user_id, group_id FROM group_members")
    members = cursor.fetchall()
    if data["user_id"] in members:
        return return_400_error_response("User already in group")

    
    # Fetch group_id using group_name
    cursor.execute("SELECT group_id FROM `groups` WHERE group_name = %s AND created_by = %s", (data["group_name"], group_creator_id,))
    group_id = cursor.fetchone()[0]
    print("group_id: ", group_id)


    # Add user as member to group
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id) VALUES (%s, %s)",
        (group_id, data["user_id"]),
    )

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"success": True, "message": "Group member added successfully"}), 201
