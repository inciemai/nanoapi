from flask import Blueprint, request, jsonify
from config import db
from utils.auth import token_required, verify_token as verify_token_func

verify_token_bp = Blueprint('verify_token', __name__)

@verify_token_bp.route('/verify-token', methods=['GET'])
@token_required
def verify_token_endpoint():
    """Get current user details from token (protected endpoint)"""
    try:
        user_data = request.current_user
        
        return jsonify({
            'status': 'success',
            'message': 'Token is valid',
            'user_data': {
                'user_id': user_data.get('user_id'),
                'name': user_data.get('name'),
                'email': user_data.get('email'),
                'phone': user_data.get('phone'),
                'role': user_data.get('role'),
                'school': user_data.get('school')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

