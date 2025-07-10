from flask import request, jsonify
import uuid
from datetime import datetime, date

from config.dbconfig import get_connection
from helper_functions import (
    auth_required,
    return_200_response,
    return_400_error_response,
    return_404_not_found,
)
from . import expenses_bp
from group_members.group_members_get import get_group_members_helper


def get_expense_date_object(expense):
    if isinstance(expense["expense_date"], date):
        expense["expense_date"] = expense["expense_date"].strftime("%d-%m-%Y")
        return expense


def get_created_at_datetime_object(expense):
    if isinstance(expense["created_at"], datetime):
        expense["created_at"] = expense["created_at"].strftime("%d-%m-%Y")
        return expense


@expenses_bp.route("/expenses", methods=["GET"])
@auth_required
def get_all_expenses():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    print("expenses: ", expenses)

    return (
        jsonify(
            {
                "success": True,
                "message": "Expense details fetched successfully",
                "data": {"expenses": expenses, "count": len(expenses)},
            }
        ),
        200,
    )


@expenses_bp.route("/expenses/<string:expense_id>", methods=["GET"])
@auth_required
def get_expense_details_by_expense_id(expense_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT paid_by, description, amount, expense_date, created_at FROM expenses WHERE expense_id = %s",
        (expense_id,),
    )
    expense = cursor.fetchone()
    if not expense:
        return return_404_not_found("Expense not found")

    expense = get_expense_date_object(expense)
    expense = get_created_at_datetime_object(expense)

    cursor.execute(
        """
        SELECT s.user_id, s.amount_owed, u.first_name
        FROM expense_shares s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.expense_id = %s
    """,
        (expense_id,),
    )
    shares_raw = cursor.fetchall()

    # Format shares into a flat list
    shares = [
        {
            "id": row["user_id"],
            "name": row["first_name"],
            "share_amount": float(row["amount_owed"]),
        }
        for row in shares_raw
    ]

    return return_200_response(
        "Expense details fetched successfully", {"expense": expense, "shares": shares}
    )


@expenses_bp.route("/expenses/group/<string:group_id>", methods=["GET"])
@auth_required
def get_all_expenses_for_a_group(group_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM expenses WHERE group_id = %s", (group_id,))
    expenses = cursor.fetchall()

    for expense in expenses:
        expense = get_expense_date_object(expense)
        expense = get_created_at_datetime_object(expense)

        cursor.execute(
            """
            SELECT s.user_id, s.amount_owed, u.first_name
            FROM expense_shares s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.expense_id = %s
        """,
            (expense["expense_id"],),
        )
        shares_raw = cursor.fetchall()

        # Format shares into a flat list
        shares = [
            {
                "id": row["user_id"],
                "name": row["first_name"],
                "share_amount": float(row["amount_owed"]),
            }
            for row in shares_raw
        ]

        expense["shares"] = shares

    for expense in expenses:
        cursor.execute(
            "SELECT first_name FROM users WHERE user_id = %s", (expense["paid_by"],)
        )
        user = cursor.fetchone()
        expense["paid_by_name"] = user["first_name"] if user else None

    cursor.close()
    connection.close()

    return return_200_response(
        "All expenses for group fetched successfully", {"expenses": expenses}
    )
