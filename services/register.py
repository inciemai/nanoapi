from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from config import db, EMAIL_REGEX, PHONE_REGEX, ADMIN_USERNAME, ADMIN_PASSWORD

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['POST'])
def register():
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email_id', 'phone', 'password', 'confirm_password', 'school']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'status': False, 'error': f'{field} is required'}), 400
        
        name = data['name']
        email_id = data['email_id'].lower()  # Email ID
        phone = data['phone']
        password = data['password']
        confirm_password = data['confirm_password']
        school = data['school']
        
        # Validate password match
        if password != confirm_password:
            return jsonify({'status': False, 'error': 'Password and confirm password do not match'}), 400
        
        # Validate email format
        if not EMAIL_REGEX.match(email_id):
            return jsonify({'status': False, 'error': 'Invalid email format'}), 400
        
        # Validate phone number format
        if not PHONE_REGEX.match(phone):
            return jsonify({'status': False, 'error': 'Invalid phone number. Must be in format +91-XXXXXXXXXX'}), 400
        
        # Check if user already exists
        existing_user = db.users.find_one({'$or': [{'email': email_id}, {'phone': phone}]})
        if existing_user:
            return jsonify({'status': False, 'error': 'User with this email or phone already exists'}), 409
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Check if admin credentials
        if email_id == ADMIN_USERNAME.lower() and password == ADMIN_PASSWORD:
            role = 'admin'
        else:
            role = 'user'
        
        # Create user document
        user_doc = {
            'name': name,
            'email': email_id,
            'phone': phone,
            'password': hashed_password,
            'role': role,
            'school': school
        }

        result = db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        return jsonify({
            'status': True,
            'message': 'User registered successfully',
            'data': {
                'user_id': user_id,
                'name': name,
                'email_id': email_id,
                'phone': phone,
                'school': school,
                'role': role
            }
        }), 201
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

