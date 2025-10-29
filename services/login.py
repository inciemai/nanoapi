from flask import Blueprint, request, jsonify
from pymongo.errors import PyMongoError
import re
from werkzeug.security import check_password_hash
from config import db, ADMIN_USERNAME, ADMIN_PASSWORD
from utils.auth import generate_token

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    try:
      
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        
        # Validate required fields
        if 'username' not in data or 'password' not in data:
            return jsonify({'status': False, 'error': 'Username/Email and password are required'}), 400
        
        username_or_email = data['username'].lower()
        password = data['password']
        
        # Auto-login for admin user (username match only)
        if username_or_email == ADMIN_USERNAME.lower():
            # Generate admin token
            user_id = 'admin'
            user_role = 'admin'
            token = generate_token(
                user_id, 
                user_role,
                name='Administrator',
                email=ADMIN_USERNAME,
                # phone='',
                # school=''
            )

            return jsonify({
                'status': True,
                'message': 'Login successful',
                'token': token,
                'user': {
                    'user_id': user_id,
                    'name': 'Administrator',
                    'username': ADMIN_USERNAME,
                    'phone': '',
                    'school': '',
                    'role': 'admin'
                }
            }), 200
        
        # Find user by username, email, or name (case-insensitive)
        user = db.users.find_one({
            '$or': [
                {'email': username_or_email}, 
                {'name': {'$regex': f'^{re.escape(username_or_email)}$', '$options': 'i'}}
            ]
        })
        
        if not user:
            return jsonify({'status': False, 'error': 'Invalid username/email or password'}), 401
        
        # Verify password
        if not check_password_hash(user['password'], password):
            return jsonify({'status': False, 'error': 'Invalid username/email or password'}), 401
        
        # Generate JWT token with all user details
        user_id = str(user['_id'])
        user_role = user.get('role', 'user')  # Default to 'user' for regular users
        token = generate_token(
            user_id, 
            user_role,
            name=user.get('name', ''),
            email=user.get('email', ''),
            phone=user.get('phone', ''),
            school=user.get('school', '')
        )
        
        # Login successful
        return jsonify({
            'status': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user_id,
                'name': user['name'],
                'username': user['email'],  # email field contains username/email
                'phone': user['phone'],
                'school': user.get('school', ''),
                'role': user_role
            }
        }), 200
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

