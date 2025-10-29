from flask import Blueprint, request, jsonify
from bson import ObjectId
from config import db
from utils.auth import token_required

get_user_bp = Blueprint('get_user', __name__)

@get_user_bp.route('/user/<user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            return jsonify({'status': False, 'error': 'Invalid user ID'}), 400
        
        # Find user by ID, exclude password
        user = db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
        
        if not user:
            return jsonify({'status': False, 'error': 'User not found'}), 404
        
        # Convert ObjectId to string
        user['_id'] = str(user['_id'])
        
        # Check if user has attempted any quiz
        has_attempted = db.quiz_results.count_documents({'user_id': user_id}) > 0
        user['is_quiz_attempted'] = has_attempted
        
        return jsonify({'status': True, 'user': user}), 200
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

