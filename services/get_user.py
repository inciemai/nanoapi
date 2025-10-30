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
        
        # --- New fields calculation start ---
        # 1. Total questions in all quizzes
        total_questions = 0
        for quiz in db.quizzes.find({}, {'questions': 1}):
            total_questions += len(quiz.get('questions', []))

        # 2. All quiz results for this user
        user_quiz_results = list(db.quiz_results.find({'user_id': user_id}))
        total_questions_attempted = sum(len(res.get('questions', [])) for res in user_quiz_results)
        time_taken = sum(res.get('time_taken', 0) for res in user_quiz_results)
        total_correct = sum(res.get('correct_answers', 0) for res in user_quiz_results)
        total_questions_for_user = sum(res.get('total_questions', 0) for res in user_quiz_results)

        # 3. Rank calculation
        user_scores = {}  # key: user_id, value: total_correct
        for res in db.quiz_results.find({}):
            uid = res['user_id']
            user_scores[uid] = user_scores.get(uid, 0) + res.get('correct_answers', 0)
        sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
        rank = next((index + 1 for index, (uid, _) in enumerate(sorted_users) if uid == user_id), None)
        # --- New fields calculation end ---
        
        if not user:
            return jsonify({'status': False, 'error': 'User not found'}), 404
        
        # Convert ObjectId to string
        user['_id'] = str(user['_id'])
        # Attach extra fields to user dict
        user['total_questions'] = total_questions
        user['total_questions_attempted'] = total_questions_attempted
        user['rank'] = rank
        user['time_taken'] = time_taken
        user['score'] = {
            'total_correct': total_correct,
            'total_questions': total_questions_for_user
        }
        
        # Check if user has attempted any quiz
        has_attempted = db.quiz_results.count_documents({'user_id': user_id}) > 0
        user['is_quiz_attempted'] = has_attempted
        
        return jsonify({'status': True, 'user': user}), 200
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

