from flask import Blueprint, request, jsonify
from config import db
from utils.auth import admin_required

get_users_bp = Blueprint('get_users', __name__)

@get_users_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        users = db.users.find({}, {'password': 0})  # Exclude password field
        user_list = []
        for user in users:
            user['_id'] = str(user['_id'])
            user_list.append(user)
        return jsonify({'users': user_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

