from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from config import db
from utils.auth import admin_required

delete_question_bp = Blueprint('delete_question', __name__)

@delete_question_bp.route('/quiz/<quiz_id>/question/<question_id>', methods=['DELETE'])
@admin_required
def delete_question(quiz_id, question_id):
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        # Validate quiz ObjectId
        if not ObjectId.is_valid(quiz_id):
            return jsonify({'status': False, 'error': 'Invalid quiz ID'}), 400
        
        # Check if quiz exists
        quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
        if not quiz:
            return jsonify({'status': False, 'error': 'Quiz not found'}), 404
        
        # Get questions array
        questions = quiz.get('questions', [])
        
        # Check if quiz has any questions
        if not questions or len(questions) == 0:
            return jsonify({'status': False, 'error': 'Quiz has no questions to delete'}), 400
        
        # Find the question to delete
        question_to_delete = None
        question_index = -1
        
        for idx, question in enumerate(questions):
            if question.get('question_id') == question_id:
                question_to_delete = question
                question_index = idx
                break
        
        if question_to_delete is None:
            return jsonify({'status': False, 'error': 'Question not found in quiz'}), 404
        
        # Store question info before deletion for response
        deleted_question_info = {
            'question_id': question_id,
            'question': question_to_delete.get('question', 'Unknown'),
            'options': question_to_delete.get('options', [])
        }
        
        # Remove the question from the array
        questions.pop(question_index)
        
        # Check if there are questions left (quiz should have at least one question)
        if len(questions) == 0:
            return jsonify({
                'status': False, 
                'error': 'Cannot delete the last question. Quiz must have at least one question. Delete the entire quiz instead.'
            }), 400
        
        # Get admin user info from token
        admin_user = request.current_user
        
        # Update the quiz with the new questions array
        update_fields = {
            'questions': questions,
            'total_questions': len(questions),
            'updated_at': datetime.now().isoformat(),
            'updated_by': admin_user.get('name', 'Administrator')
        }
        
        result = db.quizzes.update_one(
            {'_id': ObjectId(quiz_id)},
            {'$set': update_fields}
        )
        
        if result.modified_count == 0:
            return jsonify({'status': False, 'error': 'Failed to delete question'}), 500
        
        return jsonify({
            'status': True,
            'message': 'Question deleted successfully',
            'data': {
                'quiz_id': str(quiz['_id']),
                'quiz_title': quiz.get('title', 'Unknown'),
                'deleted_question': deleted_question_info,
                'remaining_questions': len(questions),
                'total_questions': len(questions)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

