from flask import request, jsonify
import uuid

from config.dbconfig import get_connection
from helper_functions import (
    auth_required,
    return_400_error_response,
    return_404_not_found,
)
from . import expenses_bp
from group_members.group_members_get import get_group_members_helper


@expenses_bp.route("/expenses", methods=["POST"])
@auth_required
def add_new_expense():
    connection = get_connection()
    cursor = connection.cursor()

    auth_user = request.user["user_id"]
    data = request.get_json()
    splits = data["splits"]

    # Fetching data
    cursor.execute(
        "SELECT group_id FROM `groups` WHERE group_name = %s", (data["group_name"],)
    )
    group_id = cursor.fetchone()[0]

    # Validating Input Data
    if (
        not data["group_name"]
        or not data["description"]
        or not data["amount"]
        or not data["expense_date"]
    ):
        return return_400_error_response("Missing required param")
    print("Input data validation complete.")


    if not splits or not isinstance(splits, list):
        return return_400_error_response("Invalid splits array")
    print("splits array validation check complete.")


    # members_in_group = get_group_members_helper(auth_user, group_id)
    total_of_shares = round(sum(float(s["share_amount"]) for s in splits), 2)
    if total_of_shares != data["amount"]:
        return return_400_error_response("Incorrect splits added")
    print("Total share calculation and validation, complete.")


    if any("share_amount" not in split for split in splits):
        return return_400_error_response("Each split must include 'share_amount'")
    print("Share amount validation, complete.")


    # Insert into expenses table
    expense_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO expenses (expense_id, group_id, paid_by, description, amount, expense_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """,
        (
            expense_id,
            group_id,
            data["paid_by"],
            data["description"],
            data["amount"],
            data["expense_date"],
        ),
    )
    print("Successfully inserted data into expenses table. ")


    # Insert shares into expense_shares table
    for split in splits:
        user_id = split["user_id"]
        paid_by = data["paid_by"]
        share_amount = float(split["share_amount"])
        # print("paid_by: ", paid_by)

        if paid_by == user_id:
            share_amount = -share_amount
            cursor.execute(
                """
                INSERT INTO expense_shares (expense_id, user_id, owes_to, amount_owed, group_id)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (expense_id, user_id, None, share_amount, group_id),
            )
        else:
            # print(user_id, "'s share_amount: ", share_amount)
            cursor.execute(
                """
                INSERT INTO expense_shares (expense_id, user_id, owes_to, amount_owed, group_id)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (expense_id, user_id, paid_by, share_amount, group_id),
            )
    print("Successfully inserted data into expense shares table. ")

        # cursor.execute("""
        #     INSERT INTO expense_shares (expense_id, user_id, amount_owed)
        #     VALUES (%s, %s, %s)
        # """, (expense_id, user_id, share_amount))

    connection.commit()
    cursor.close()
    connection.close()

    return (
        jsonify(
            {
                "success": True,
                "message": "Expense added successfully",
                "data": {"expense_id": expense_id},
            }
        ),
        201,
    )
