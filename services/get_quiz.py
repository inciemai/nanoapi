from flask import Blueprint, request, jsonify
from bson import ObjectId
from config import db
from utils.auth import token_required

get_quiz_bp = Blueprint('get_quiz', __name__)

@get_quiz_bp.route('/quiz/<quiz_id>', methods=['GET'])
@token_required
def get_quiz(quiz_id):
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        # Validate ObjectId
        if not ObjectId.is_valid(quiz_id):
            return jsonify({'status': False, 'error': 'Invalid quiz ID'}), 400
        
        quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
        
        if not quiz:
            return jsonify({'status': False, 'error': 'Quiz not found'}), 404
        
        quiz['_id'] = str(quiz['_id'])
        # Don't send correct answers to prevent cheating, but keep question_id
        for question in quiz['questions']:
            # Ensure question_id is included, remove only correct_answer
            if 'correct_answer' in question:
                question.pop('correct_answer', None)
        
        return jsonify({'status': True, 'quiz': quiz}), 200
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

