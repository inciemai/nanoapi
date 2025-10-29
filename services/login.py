from flask import Blueprint, request, jsonify
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
        if 'email' not in data or 'password' not in data:
            return jsonify({'status': False, 'error': 'Email and password are required'}), 400
        
        email = data['email'].lower()
        password = data['password']
        
        # Check for admin login first (allows username instead of email)
        if email == ADMIN_USERNAME.lower():
            # Verify admin password
            if password != ADMIN_PASSWORD:
                return jsonify({'status': False, 'error': 'Invalid username or password'}), 401
            
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
        
        # Basic email validation for regular users
        if '@' not in email:
            return jsonify({'status': False, 'error': 'Invalid email format'}), 400
        
        # Find user by email only (case-insensitive)
        user = db.users.find_one({'email': email})
        
        if not user:
            return jsonify({'status': False, 'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not check_password_hash(user['password'], password):
            return jsonify({'status': False, 'error': 'Invalid email or password'}), 401
        
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
                'username': user['email'],  
                'phone': user['phone'],
                'school': user.get('school', ''),
                'role': user_role
            }
        }), 200
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

