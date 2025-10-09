from flask import jsonify
from config.dbconfig import get_connection
from helper_functions import auth_required, return_404_not_found
from . import expenses_bp


@expenses_bp.route("/expenses/<expense_id>", methods=["DELETE"])
@auth_required
def delete_expense(expense_id):
    connection = get_connection()
    cursor = connection.cursor()

    # Check if expense exists
    cursor.execute("SELECT * FROM expenses WHERE expense_id = %s", (expense_id,))
    existing_expense = cursor.fetchone()
    if not existing_expense:
        return return_404_not_found("Expense not found")

    # Delete all related expense_shares first (to avoid foreign key issues)
    cursor.execute("DELETE FROM expense_shares WHERE expense_id = %s", (expense_id,))

    # Delete the expense itself
    cursor.execute("DELETE FROM expenses WHERE expense_id = %s", (expense_id,))

    connection.commit()
    cursor.close()
    connection.close()

    return (
        jsonify(
            {
                "success": True,
                "message": "Expense deleted successfully",
                "data": {"expense_id": expense_id},
            }
        ),
        204,
    )
