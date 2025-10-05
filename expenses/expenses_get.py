from flask import request, jsonify
import uuid
from datetime import datetime, date
from collections import defaultdict

from config.dbconfig import get_connection
from helper_functions import (
    auth_required,
    return_200_response,
    return_400_error_response,
    return_404_not_found,
    get_user_name_by_user_id,
    get_group_name_from_group_id,
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
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

    for expense in expenses:
        name = get_user_name_by_user_id(cursor, expense["paid_by"])
        expense["paid_by"] = name

    for expense in expenses:
        group_id = expense.pop("group_id")
        expense.pop("expense_id")
        group_name = get_group_name_from_group_id(cursor, group_id)
        expense["group_name"] = group_name

    return return_200_response(
        "Expense details fetched successfully",
        {"expenses": expenses, "count": len(expenses)},
    )


@expenses_bp.route("/expenses/<string:expense_id>", methods=["GET"])
@auth_required
def get_expense_details_by_expense_id(expense_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT paid_by, description, amount, expense_date, created_at, updated_at FROM expenses WHERE expense_id = %s",
        (expense_id,),
    )
    expense = cursor.fetchone()
    if not expense:
        return return_404_not_found("Expense not found")

    expense = get_expense_date_object(expense)
    expense = get_created_at_datetime_object(expense)
    expense["paid_by"] = get_user_name_by_user_id(cursor, expense["paid_by"])

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
            "user_id": row["user_id"],
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

    group_name = get_group_name_from_group_id(cursor, group_id)

    cursor.execute("SELECT * FROM expenses WHERE group_id = %s", (group_id,))
    expenses = cursor.fetchall()

    for expense in expenses:
        expense.pop("group_id")
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
                "user_id": row["user_id"],
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
        expense["paid_by"] = get_user_name_by_user_id(
            cursor, expense["paid_by"]
        )
        # expense["paid_by_name"] = user["first_name"] if user else None

    cursor.close()
    connection.close()

    return return_200_response(
        "All expenses for group fetched successfully",
        {"count": len(expenses), "group_name": group_name, "expenses": expenses},
    )


@expenses_bp.route("/user/balances", methods=["GET"])
@auth_required
def get_user_balances():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    auth_user = request.user["user_id"]

    cursor.execute("""
        SELECT user_id, SUM(amount_owed) AS total_receiving
        FROM expense_shares
        WHERE owes_to = %s
        GROUP BY user_id
    """, (auth_user,))
    results = cursor.fetchall()


    amount_receiving = 0
    receives_list = {}
    for result in results:
        amount_receiving += float(result["total_receiving"])
        name = get_user_name_by_user_id(cursor, result["user_id"])
        receives_list[name] = float(result["total_receiving"])
    

    cursor.execute("""
        SELECT owes_to, SUM(amount_owed) AS total_owed
        FROM expense_shares
        WHERE user_id = %s AND owes_to IS NOT NULL
        GROUP BY owes_to
    """, (auth_user,))
    results = cursor.fetchall()


    amount_owed = 0
    owes_list = {}
    for result in results:
        amount_owed += float(result["total_owed"])
        name = get_user_name_by_user_id(cursor, result["owes_to"])
        owes_list[name] = float(result["total_owed"])


    net_balances = defaultdict(float)
    for user, amount in receives_list.items():
        net_balances[user] += amount  # money they owe you
    for user, amount in owes_list.items():
        net_balances[user] -= amount  # money you owe them


    data = {
        "balance": amount_receiving - amount_owed,
        "net_balances": net_balances
    }

    return return_200_response("yay", data)
