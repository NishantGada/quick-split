from flask import jsonify
from config.dbconfig import get_connection

def is_duplicate_email(email):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    email = cursor.fetchone()
    if email:
        return True
    return False
