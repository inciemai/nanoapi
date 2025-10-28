from flask import Flask, request, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from dotenv import load_dotenv
import os
import re
from datetime import datetime, timedelta
try:
    import jwt
except ImportError:
    print("PyJWT not found. Please install it with: pip install PyJWT")
    jwt = None
from functools import wraps

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 8766

# Static Admin Credentials (Change these as needed)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "userdb")

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    # Test the connection
    client.server_info()
    print(f"Connected to MongoDB successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Phone number validation regex (+91-One digit-9 digits)
PHONE_REGEX = re.compile(r'^\+91-\d{10}$')


# JWT Helper Functions
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


# Authentication Decorators
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


@app.route('/register', methods=['POST'])
def register():
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email_id', 'phone', 'password', 'confirm_password', 'school']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        name = data['name']
        email_id = data['email_id'].lower()  # Email ID
        phone = data['phone']
        password = data['password']
        confirm_password = data['confirm_password']
        school = data['school']
        
        # Validate password match
        if password != confirm_password:
            return jsonify({'error': 'Password and confirm password do not match'}), 400
        
        # Validate email format
        if not EMAIL_REGEX.match(email_id):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate phone number format
        if not PHONE_REGEX.match(phone):
            return jsonify({'error': 'Invalid phone number. Must be in format +91-XXXXXXXXXX'}), 400
        
        # Check if user already exists
        existing_user = db.users.find_one({'$or': [{'email': email_id}, {'phone': phone}]})
        if existing_user:
            return jsonify({'error': 'User with this email or phone already exists'}), 409
        
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
        
        # Insert into MongoDB
        result = db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        return jsonify({
            'status': 'success',
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
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        
        # Validate required fields
        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username/Email and password are required'}), 400
        
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
                phone='',
                school=''
            )
            
            # Admin login successful
            return jsonify({
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
            return jsonify({'error': 'Invalid username/email or password'}), 401
        
        # Verify password
        if not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid username/email or password'}), 401
        
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
        return jsonify({'error': str(e)}), 500


@app.route('/users', methods=['GET'])
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


@app.route('/quiz', methods=['POST'])
@admin_required
def create_quiz():
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        
        # Get admin user info from token
        admin_user = request.current_user
        created_by = admin_user.get('name', 'Administrator')
        
        # Only require questions array
        if 'questions' not in data or not data['questions']:
            return jsonify({'error': 'questions array is required'}), 400
        
        title = data.get('title', 'Quiz')
        questions = data['questions']
        
        # Validate questions
        if not isinstance(questions, list) or len(questions) == 0:
            return jsonify({'error': 'Questions must be a non-empty array'}), 400
        
        # Validate each question - only require question, options, and correct_answer
        for idx, question in enumerate(questions):
            if 'question' not in question or not question['question']:
                return jsonify({'error': f'Question {idx + 1} must have question field'}), 400
            
            if 'options' not in question or not isinstance(question['options'], list) or len(question['options']) < 2:
                return jsonify({'error': f'Question {idx + 1} must have at least 2 options'}), 400
            
            if 'correct_answer' not in question or question['correct_answer'] not in question['options']:
                return jsonify({'error': f'Question {idx + 1} must have a correct_answer that matches one of the options'}), 400
        
        # Create quiz document with simplified question format
        quiz_doc = {
            'title': title,
            'questions': questions,
            'created_by': created_by,
            'created_at': datetime.now().isoformat(),
            'total_questions': len(questions)
        }
        
        # Insert into MongoDB
        result = db.quizzes.insert_one(quiz_doc)
        
        return jsonify({
            'status': 'success',
            'message': 'Quiz created successfully',
            'data': {
                'quiz_id': str(result.inserted_id),
                'title': title,
                'total_questions': len(questions),
                'created_by': created_by,
                'created_at': quiz_doc['created_at']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/quizzes', methods=['GET'])
def get_quizzes():
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get optional query parameters
        created_by = request.args.get('created_by')
        
        query = {}
        if created_by:
            query['created_by'] = created_by
        
        quizzes = db.quizzes.find(query).sort('created_at', -1)
        quiz_list = []
        for quiz in quizzes:
            quiz['_id'] = str(quiz['_id'])
            # Don't send correct answers in the list view
            for question in quiz['questions']:
                question.pop('correct_answer', None)
            quiz_list.append(quiz)
        
        return jsonify({
            'quizzes': quiz_list,
            'total': len(quiz_list)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/quiz/<quiz_id>', methods=['GET'])
@token_required
def get_quiz(quiz_id):
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Validate ObjectId
        if not ObjectId.is_valid(quiz_id):
            return jsonify({'error': 'Invalid quiz ID'}), 400
        
        quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
        
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        quiz['_id'] = str(quiz['_id'])
        # Don't send correct answers to prevent cheating
        for question in quiz['questions']:
            question.pop('correct_answer', None)
        
        return jsonify({'quiz': quiz}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/quiz/<quiz_id>/submit', methods=['POST'])
@token_required
def submit_quiz(quiz_id):
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Validate ObjectId
        if not ObjectId.is_valid(quiz_id):
            return jsonify({'error': 'Invalid quiz ID'}), 400
        
        # Get quiz from database
        quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
        
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        data = request.get_json()
        
        # Validate answers
        if 'answers' not in data or not isinstance(data['answers'], list):
            return jsonify({'error': 'Answers must be provided as an array'}), 400
        
        # Validate and get time field
        time_taken = data.get('time', 0)  # Get time field, default to 0 if not provided
        if not isinstance(time_taken, (int, float)) or time_taken < 0:
            return jsonify({'error': 'Time must be a positive number'}), 400
        
        answers = data['answers']
        user_id = request.current_user.get('user_id')  # Get from token
        
        # Score the quiz
        correct_count = 0
        total_questions = len(quiz['questions'])
        questions_with_answers = []
        
        for idx, question in enumerate(quiz['questions']):
            user_answer = answers[idx] if idx < len(answers) else None
            # Compare answers case-insensitively
            is_correct = str(user_answer).strip().lower() == str(question['correct_answer']).strip().lower()
            
            if is_correct:
                correct_count += 1
            
            # Prepare question with user's answer and correctness
            question_response = {
                'question': question['question'],
                'options': question['options'],
                'correct_answer': question['correct_answer'],
                'user_answer': user_answer,
                'is_correct': is_correct
            }
            questions_with_answers.append(question_response)
        
        # Store result
        result_doc = {
            'quiz_id': quiz_id,
            'user_id': user_id,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'time_taken': time_taken,
            'questions': questions_with_answers,
            'submitted_at': datetime.now().isoformat()
        }
        
        db.quiz_results.insert_one(result_doc)
        
        return jsonify({
            'status': 'success',
            'message': 'Quiz submitted successfully',
            'result': {
                'score': f'{correct_count}/{total_questions}',
                'correct_answers': correct_count,
                'total_questions': total_questions,
                'time_taken': time_taken
            },
            'questions': questions_with_answers
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/decode-token', methods=['POST'])
def decode_token():
    """Decode JWT token and show all user details"""
    try:
        data = request.get_json()
        
        if 'token' not in data:
            return jsonify({'error': 'Token is required'}), 400
        
        token = data['token']
        
        # Verify and decode token
        payload = verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
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
        return jsonify({'error': str(e)}), 500


@app.route('/verify-token', methods=['GET'])
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



if __name__ == '__main__':
    # app.run(debug=True, port=5000)
    app.run(host="0.0.0.0", port=5000)
