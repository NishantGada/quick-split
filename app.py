from flask import Flask, request, jsonify
from flask_cors import CORS

from config.dbconfig import *
from auth import auth_bp
from groups import groups_bp
from group_members import group_members_bp
from expenses import expenses_bp
from users import users_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(users_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(group_members_bp)
app.register_blueprint(expenses_bp)

@app.route('/')
def root():
    return jsonify({"message": "Welcome to Xpense"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
