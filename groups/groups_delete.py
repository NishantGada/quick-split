from flask import request, jsonify

from config.dbconfig import get_connection
from helper_functions import (
    auth_required,
    return_400_error_response,
    return_200_response,
)
from . import groups_bp
from group_members.group_members_get import get_group_members_helper
from expenses.expenses_get import get_user_balances_based_on_group_id_helper


@groups_bp.route("/groups/<string:group_id>", methods=["DELETE"])
@auth_required
def delete_group(group_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))

        cursor.execute("DELETE FROM `groups` WHERE group_id = %s", (group_id,))

        connection.commit()
        cursor.close()
        connection.close()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Deleted group successfully",
                }
            ),
            204,
        )

    except Exception as e:
        return return_400_error_response(e)
