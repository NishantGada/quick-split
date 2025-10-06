from flask import request, jsonify

from config.dbconfig import get_connection
from helper_functions import auth_required, return_400_error_response
from . import groups_bp
from group_members.group_members_get import get_group_members_helper
from expenses.expenses_get import get_user_balances_based_on_group_id_helper


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

    auth_user = request.user["user_id"]
    for group in groups:
        try:
            members, group_name, error = get_group_members_helper(auth_user, group["group_id"])
            group_balance_data = get_user_balances_based_on_group_id_helper(cursor, auth_user, group["group_id"])
            group["member_count"] = len(members)
            group["group_balance_data"] = group_balance_data
        except Exception as e:
            return return_400_error_response(e)

    return (
        jsonify(
            {
                "success": True,
                "message": "All groups fetched successfully",
                "data": {"groups": groups},
            }
        ),
        200,
    )
