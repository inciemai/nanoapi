import jwt
from datetime import datetime, timedelta
from flask import request, jsonify
from functools import wraps
from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS

def generate_token(user_id, role, name="", email="", phone="", school=""):
    """Generate JWT token for user with all details"""
    payload = {
        'user_id': user_id,
        'role': role,
        'name': name,
        'email': email,
        'phone': phone,
        'school': school,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    try:
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        # PyJWT 2.x returns string, 1.x returns bytes
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
    except Exception as e:
        print(f"Error generating token: {e}")
        raise


def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_header():
    """Extract token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0] != 'Bearer':
        return None
    
    return parts[1]


def token_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Add user info to request
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        if payload.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated

