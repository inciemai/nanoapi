from flask import Blueprint, request, jsonify
from bson import ObjectId
from config import db
from utils.auth import admin_required

delete_quiz_bp = Blueprint('delete_quiz', __name__)

@delete_quiz_bp.route('/quiz/<quiz_id>', methods=['DELETE'])
@admin_required
def delete_quiz(quiz_id):
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        # Validate ObjectId
        if not ObjectId.is_valid(quiz_id):
            return jsonify({'status': False, 'error': 'Invalid quiz ID'}), 400
        
        # Check if quiz exists
        quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
        if not quiz:
            return jsonify({'status': False, 'error': 'Quiz not found'}), 404
        
        # Store quiz info before deletion for response
        quiz_info = {
            'quiz_id': str(quiz['_id']),
            'title': quiz.get('title', 'Unknown'),
            'total_questions': quiz.get('total_questions', len(quiz.get('questions', [])))
        }
        
        # Delete the quiz
        result = db.quizzes.delete_one({'_id': ObjectId(quiz_id)})
        
        if result.deleted_count == 0:
            return jsonify({'status': False, 'error': 'Failed to delete quiz'}), 500
        
        return jsonify({
            'status': True,
            'message': 'Quiz deleted successfully',
            'data': quiz_info
        }), 200
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

