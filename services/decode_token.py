from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.auth import verify_token

decode_token_bp = Blueprint('decode_token', __name__)

@decode_token_bp.route('/decode-token', methods=['POST'])
def decode_token():
    """Decode JWT token and show all user details"""
    try:
        data = request.get_json()
        
        if 'token' not in data:
            return jsonify({'status': False, 'error': 'Token is required'}), 400
        
        token = data['token']
        
        # Verify and decode token
        payload = verify_token(token)
        
        if not payload:
            return jsonify({'status': False, 'error': 'Invalid or expired token'}), 401
        
        return jsonify({
            'status': 'success',
            'message': 'Token decoded successfully',
            'user_data': {
                'user_id': payload.get('user_id'),
                'name': payload.get('name'),
                'email': payload.get('email'),
                'phone': payload.get('phone'),
                'role': payload.get('role'),
                'school': payload.get('school'),
                'issued_at': datetime.fromtimestamp(payload.get('iat')).isoformat() if payload.get('iat') else None,
                'expires_at': datetime.fromtimestamp(payload.get('exp')).isoformat() if payload.get('exp') else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

