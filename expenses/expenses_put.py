from flask import request, jsonify
import uuid

from config.dbconfig import get_connection
from helper_functions import (
    auth_required,
    return_400_error_response,
    return_404_not_found,
)
from . import expenses_bp


@expenses_bp.route("/expenses/<expense_id>", methods=["PUT"])
@auth_required
def update_expense(expense_id):
    connection = get_connection()
    cursor = connection.cursor()

    auth_user = request.user["user_id"]
    data = request.get_json()
    splits = data.get("splits")

    # Fetch existing expense
    cursor.execute("SELECT * FROM expenses WHERE expense_id = %s", (expense_id,))
    existing_expense = cursor.fetchone()
    if not existing_expense:
        return return_404_not_found("Expense not found")

    # Validate required fields
    required_fields = ["group_name", "description", "amount", "expense_date", "paid_by"]
    if not all(data.get(field) for field in required_fields):
        return return_400_error_response("Missing required parameter(s)")

    if not splits or not isinstance(splits, list):
        return return_400_error_response("Invalid or missing splits array")

    total_of_shares = round(sum(float(s["share_amount"]) for s in splits), 2)
    if total_of_shares != float(data["amount"]):
        return return_400_error_response(
            "Incorrect splits — sum of shares does not match total amount"
        )

    if any("share_amount" not in split for split in splits):
        return return_400_error_response("Each split must include 'share_amount'")

    # Fetch group_id for given group_name
    cursor.execute(
        "SELECT group_id FROM `groups` WHERE group_name = %s", (data["group_name"],)
    )
    group_record = cursor.fetchone()
    if not group_record:
        return return_404_not_found("Group not found")
    group_id = group_record[0]

    # Update expense record
    cursor.execute(
        """
        UPDATE expenses
        SET group_id = %s, paid_by = %s, description = %s, amount = %s, expense_date = %s
        WHERE expense_id = %s
        """,
        (
            group_id,
            data["paid_by"],
            data["description"],
            data["amount"],
            data["expense_date"],
            expense_id,
        ),
    )

    # Delete existing shares to replace with new ones
    cursor.execute("DELETE FROM expense_shares WHERE expense_id = %s", (expense_id,))

    # Insert updated shares
    for split in splits:
        user_id = split["user_id"]
        paid_by = data["paid_by"]
        share_amount = float(split["share_amount"])

        if paid_by == user_id:
            # The payer’s share is negative (they paid upfront)
            share_amount = -share_amount
            cursor.execute(
                """
                INSERT INTO expense_shares (expense_id, user_id, owes_to, amount_owed)
                VALUES (%s, %s, %s, %s)
                """,
                (expense_id, user_id, None, share_amount),
            )
        else:
            # Others owe money to the payer
            cursor.execute(
                """
                INSERT INTO expense_shares (expense_id, user_id, owes_to, amount_owed)
                VALUES (%s, %s, %s, %s)
                """,
                (expense_id, user_id, paid_by, share_amount),
            )

    connection.commit()
    cursor.close()
    connection.close()

    return (
        jsonify(
            {
                "success": True,
                "message": "Expense updated successfully",
                "data": {"expense_id": expense_id},
            }
        ),
        200,
    )
