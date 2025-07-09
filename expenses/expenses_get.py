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


@expenses_bp.route("/expenses/<string:expense_id>", methods=["GET"])
@auth_required
def get_expense_details_by_expense_id(expense_id):
    connection = get_connection()
    cursor = connection.cursor()

    auth_user = request.user["user_id"]
    data = request.get_json()
    splits = data["splits"]

    # Fetching data
    cursor.execute("SELECT group_id FROM `groups` WHERE group_name = %s", (data["group_name"],))
    group_id = cursor.fetchone()[0]


    # Validating Input Data
    if not data["group_name"] or not data["description"] or not data["amount"] or not data["expense_date"]:
        print("data: ", data)
        return return_400_error_response("Missing required param")
    
    if not splits or not isinstance(splits, list):
        return return_400_error_response("Invalid splits array")
    
    members_in_group = get_group_members_helper(auth_user, group_id)
    if len(splits) != len(members_in_group):
        return return_400_error_response("Incorrect splits added. Probably missing a user's split. ")
    
    if any("share_amount" not in split for split in splits):
        return return_400_error_response("Each split must include 'share_amount'")
    
    total_share = round(sum(float(s["share_amount"]) for s in splits), 2)
    if round(data["amount"], 2) != total_share:
        return return_400_error_response("Invalid share entries. Mismatch with Total Amount")


    # Insert into expenses table
    expense_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO expenses (expense_id, group_id, paid_by, description, amount, expense_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (expense_id, group_id, auth_user, data["description"], data["amount"], data["expense_date"]))

    
    # Insert shares into expense_shares table
    for split in splits:
        user_id = split["user_id"]
        share_amount = float(split["share_amount"])

        cursor.execute("""
            INSERT INTO expense_shares (expense_id, user_id, amount_owed)
            VALUES (%s, %s, %s)
        """, (expense_id, user_id, share_amount))


    connection.commit()
    cursor.close()
    connection.close()
    

    return jsonify({"success": True, "message": "Expense added successfully"}), 201
